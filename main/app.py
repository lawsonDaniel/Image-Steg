#!usr/bin/python3

from PIL import Image
import argparse
import numpy as np
import os
import copy
import secrets

#we use INT32_MAX for our maximum bit length
"""
Image Steganography using Lowest Significant Bits (LCB) works by fliping the last two bits of a channel in an Image.
#TODO: work on Discrete Cosine Transform (DCT) AND huffman encoding.
"""
"""
Encoding constants

This are header encoding constants which will be used to define what type of data is embeded in the Image.
"""

TXT = "TXT"  #done
PNG = "PNG"  #done
JPG = "JPG"  #done
WAV = "WAV"  #work
MP3 = "MP3"  # work


def encode_audio_to_binary(audiofile):
    return NotImplementedError

def encode_text_to_binary(string):
    """
    Returns a string of bits representation of the string.
    the characters in the string are decomosed to their decimal
    value on the ASCII table. Then converted to a string of 8bit
    binary.

    args
    ----
        string: str
    
    returns
    -------
        res: str
    """
    res = ""
    for char in string:
        if type(char) == int: char = chr(char)
        ascii_dec = ord(char)
        res += return_binary(ascii_dec)
    return res


def return_binary(number, bitlen=8):
    """
    returns the binary value of a number.

    args
    ----
        number: int
        bitlen: int
    returns
    -------
        res: str
    """
    res = ""
    b = bin(number)[2:]
    res += b.zfill(bitlen)
    return res


def encode_image_to_binary(image, height, width, num_channel):
    """
    Encodes an Image to binary
    """
    res = ""
    for i in range(height):
        for j in range(width):
            for k in range(num_channel):
                value = image[i][j][k]
                res += return_binary(value)
    return res


def decode_binary_to_ascii(binary):
    """
    Returns an ascii string representation of a string of binary
    args
    ----
        binary: str
        A string of binary e.g 101001 
    returns
    -------
        str
    """
    res = ""
    for i in range(0, len(binary), 8):
        b = binary[i:i + 8]
        dec = eval(f"0b{b}")
        char = chr(dec)
        res += char
    return res


def load_image(im_dir):
    """
    Loads Image from a directory and returns the array representaion of the image and it's height and width
    args
    ----
        im_dir: str
        Image local directory
    returns
    -------
        tuple: (np.array, int, int)
    """
    im = Image.open(im_dir)
    cover_image = np.array(im)
    return cover_image, im.height, im.width


def encode_image(image, height, width, text_encoded):
    """
    Encodes the a image with a binary string and returns a encoded image array.
    args
    ----
        image: 3D np.array 
        height: int
        width: int
        text_encoded: str
    returns
    -------
        np.array 
    """
    img_copy = copy.deepcopy(image)
    prev_index = 0
    data_len = len(text_encoded)
    print(data_len)
    for i in range(height):
        for j in range(width):
            for k, channel in enumerate(img_copy[i][j]):
                if (prev_index + 2) < data_len:
                    b = return_binary(channel)
                    dec = eval(
                        f"0b{b[:6]}{text_encoded[prev_index:2+prev_index]}")
                    img_copy[i][j][k] = dec
                    prev_index += 2
                else:
                    return img_copy
    return img_copy


def get_data_len(image, num_channel):
    """
    gets the data length from header bits.
    """
    _range = image[0][:(32 // (num_channel * 2) + 1)]  #add 1 pixel to catch overlap
    res = ""
    count = 0
    for i in range(len(_range)):
        for channel in _range[i]:
            if count < 16:
                res += return_binary(channel)[-2:]
                # print(res)
                count += 1
            else:
                break
    dec = eval(f"0b{res}")
    return dec


def get_encoding_type(image, num_channel):
    """
    retrieve the encoding type of the secret message stored in the Image.
    """
    _range = image[0][(32 // (num_channel * 2)):]
    start_channel = (32 % num_channel) / 2
    res = ""
    count = 0
    for i in range(len(_range)):
        for j, channel in enumerate(_range[i]):
            if i == 0 and j < start_channel:
                continue  # skip overlap by data length bits
            if count < 12:
                res += return_binary(channel)[-2:]
                count += 1
            else:
                break
        if count >= 12:
            break

    res = decode_binary_to_ascii(res)
    return res


def get_image_data(image, starting_pixel, start_channel):
    """
    retrieve image data from image i.e height, width, channel
    """
    _range = image[0][starting_pixel:]
    res = ""
    count = 0
    for i in range(len(_range)):
        for j, channel in enumerate(_range[i]):
            if i == 0 and j < start_channel:
                continue  # skip overlap by data length bits
            if count < 40:
                res += return_binary(channel)[-2:]
                count += 2
            else:
                break
        if count >= 40:
            break
    height = eval(f"0b{res[0: 16]}")
    width = eval(f"0b{res[16: 32]}")
    channel = eval(f"0b{res[32: ]}")
    return (height, width, channel)


def decode_image(image, height, width, num_channel):
    """
    Decodes a Encoded Image and return message.
    args
    ----
        image: encoded image
        height: encoded image height
        width: encoded image width
        num_channel: encoded image number of channels.
    """
    data_len = get_data_len(image, num_channel)
    encoding = get_encoding_type(image, num_channel)
    starting_pixel = 56 // (num_channel * 2)
    start_channel = (56 % num_channel) / 2
    if encoding == PNG or encoding == JPG:
        hidden_image_height, hidden_image_width, hidden_image_channel = get_image_data(
            image, starting_pixel, start_channel)
        starting_pixel = (56 + 40) // (num_channel * 2)
        start_channel = ((56 + 40) % num_channel) / 2
    length = 0
    res = ""
    for i in range(height):
        start = 0 if i != 0 else starting_pixel  # skip header pixels
        for j in range(start, width):
            for k, channel in enumerate(image[i][j]):
                if i == 0 and j == starting_pixel and k < start_channel:
                    continue  # skip encoding overlap bits
                if length < data_len:
                    res += bin(channel)[2:].zfill(8)[-2:]
                    length += 2
                else:
                    break
            if length >= data_len: break
        if length >= data_len: break
    if encoding == TXT:
        res = decode_binary_to_ascii(res)
    if encoding == JPG or encoding == PNG:
        _image = np.zeros(
            (hidden_image_height, hidden_image_width, hidden_image_channel),
            dtype=np.uint8)
        prev_index = 0
        print(len(res))
        for i in range(hidden_image_height):
            for j in range(hidden_image_width):
                for k in range(hidden_image_channel):
                    if prev_index + 8 > len(res): break
                    _image[i][j][k] = eval(
                        f"0b{res[prev_index:prev_index+8]}")
                    prev_index += 8
        res = _image
    return res, 
    
def get_bit_space(image, iscover=False):
    """
    Calculates the total number of bits in a image and returns it
    args
    ----
        image: image to retrive info
        is_cover: if image is cover it multiplies by 2. 
    """
    n_bit = 2 if iscover else 8
    return image.shape[0] * image.shape[1] * image.shape[1] * n_bit


#height, width, channel


def main():
    """
    TO add encode images and hide data in it.
    """
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(dest="mode")
    encode_parser = subparser.add_parser("encode", help="encodes the image")
    encode_parser.add_argument("-d", dest="directory", type=str)
    encode_parser.add_argument("-t", dest="text", type=str, default="")
    encode_parser.add_argument("-i", dest="image_dir", type=str)
    encode_parser.add_argument("-f", dest="format", type=str)
    decode_parser = subparser.add_parser(
        "decode", help="decodes data hidden in image and prints it.")
    decode_parser.add_argument("-i", dest="image_dir", type=str)
    args = parser.parse_args()
    if args.mode:
        if args.image_dir:
            cover_image, height, width = load_image(args.image_dir)
            print(cover_image.shape)
            if args.mode == "encode":
                if args.format == TXT.lower():
                    text = args.text
                    if args.directory:
                        text = open(args.directory, "rb").read()
                    encoding = TXT
                    text = encode_text_to_binary(text)
                    bitlen = len(text)
                    encoding_bin = encode_text_to_binary(encoding)
                    bitlen_bin = return_binary(bitlen, 32)
                    data = bitlen_bin + encoding_bin + text
                elif args.format == PNG.lower() or args.format == JPG.lower():
                    _image, image_height, image_width = load_image(
                        args.directory)
                    assert get_bit_space(cover_image, iscover=True) > get_bit_space(_image), "Cover Image bit to small to contain image"
                    num_channel = _image.shape[-1]
                    image_bits = encode_image_to_binary(_image, image_height, image_width, num_channel)
                    bitlen = return_binary(len(image_bits), 32)
                    format = PNG if args.format == PNG.lower() else JPG
                    format_bin = encode_text_to_binary(format)
                    data = bitlen + format_bin + return_binary(image_height,16) + return_binary(image_width, 16) + return_binary(num_channel, 8) + image_bits

                else:
                    print("Input a valid format.")
                    return
                encoded_image = encode_image(cover_image, height, width, data)
                filename = os.path.basename(args.image_dir)
                filename = filename[:filename.find(".")]
                # print(encoded_image[0][:6], cover_image[0][:6])
                Image.fromarray(encoded_image.copy()).save(
                    f"encoded-{filename}.png", )
            elif args.mode == "decode":
                # print(cover_image[0][: 6 ])
                data, encoding = decode_image(cover_image, height, width,
                                              cover_image.shape[-1])
                print(encoding)
                if encoding == TXT:
                    print(data)
                elif encoding == JPG or encoding == PNG:
                    # print(data[0][:5])
                    Image.fromarray(data).save(
                        f"{secrets.token_hex(16)}.{encoding.lower()}")
        else:
            raise FileNotFoundError
    else:
        print("Please specify a mode!")


if __name__ == '__main__':
    main()
