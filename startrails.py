#!/usr/bin/env python3
import os
import numpy
import argparse
import math

from datetime import datetime
from PIL import Image


class ImageFile():
    IMAGE_COUNTER = 0

    def __init__(self, file_path: str):
        self.path = file_path
        image = Image.open(self.path)
        self.array = numpy.array(image, dtype=numpy.float)
        self.size = image.size
        ImageFile.IMAGE_COUNTER += 1
        self.num = ImageFile.IMAGE_COUNTER
        print("loaded image {}/{}: '{}'".format(
            self.num, total_image_count, self.path))

    def __del__(self):
        print("deleted image {}/{}".format(self.num, total_image_count))


class Stack():
    def __init__(self, img_range: list):
        self.img_range = img_range
        self.array = None
        self.width, self.height = (None, None)
        self._image_limit = len(img_range) - 1
        self._n_images = 0

    def add_image(self, image: Image.Image):
        if self._n_images == self._image_limit:
            Exception("Stack has already been processed & output!!!!")
        if self.array is None:
            self.width, self.height = image.size
            self.array = numpy.zeros((self.height, self.width, 3), numpy.float)
        elif image.size != (self.width, self.height):
            raise Exception("{} != {}".format(image.size, (self.width, self.height)))  # TODO include filename w/ exception

        self.array = numpy.maximum(self.array, image.array)
        self._n_images = self._n_images + 1
        print("image {}, added to stack {}".format(image.num, self.img_range))
        if self._n_images == self._image_limit:
            self.output()

    def output(self):
        if self.array is None:
            return  # maybe should log
        new_stack = numpy.array(numpy.round(self.array), dtype=numpy.uint8)
        output = Image.fromarray(new_stack, mode="RGB")
        date = datetime.now().strftime("%Y-%m-%d")
        filename = "stack_{}-{}_{}.jpeg".format(
            self.img_range.start, self.img_range.stop, date)
        output.save(filename, "JPEG")
        print("Saved stack to {}".format(filename))
        # cleanup memory footprint of this object
        self.array = None


def get_subset_of_files(files: list,
                        start_filename: str = None,
                        end_filename: str = None) -> list:
    if start_filename is None and end_filename is None:
        return files
    start_index = 0
    end_index = len(files)
    if start_filename:
        start_index = files.index(start_filename)
    if end_filename:
        end_index = files.index(end_filename)
    # both can throw ValueError
    return files[start_index:end_index]


def create_stacks_of_size(stack_size: int) -> list:
    n_stacks = math.ceil(total_image_count/stack_size)
    stacks = []
    for i in range(0, n_stacks):
        stk = Stack(range(i * stack_size, i * stack_size + stack_size))
        stacks.append(stk)
    return stacks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('--target_dir', type=str, required=True, help="")
    parser.add_argument('--start_filename', type=str, required=False, default=None, help="")
    parser.add_argument('--end_filename', type=str, required=False, default=None, help="")
    parser.add_argument('--output', type=str, required=True, help="")
    parser.add_argument('--skip_num', type=int, required=False, default=None, help="")
    args = parser.parse_args()

    if not os.path.exists(os.path.dirname(args.output)):
        raise Exception("--output path directory doesn't exist: {}".format(args.output))

    file_paths = os.listdir(args.target_dir)
    file_paths.sort()
    file_paths = get_subset_of_files(file_paths, args.start_filename, args.end_filename)

    # create full file paths w/ target_dir included
    file_paths = [args.target_dir + x for x in file_paths]
    jpeg_paths = list(filter(lambda x: x.endswith(".JPG"), file_paths))

    if args.skip_num:
        jpeg_paths = jpeg_paths[::args.skip_num]

    total_image_count = len(jpeg_paths)

    stacks_to_process = []
    stacks_to_process.extend(create_stacks_of_size(10))
    stacks_to_process.extend(create_stacks_of_size(20))
    stacks_to_process.extend(create_stacks_of_size(30))
    stacks_to_process.extend(create_stacks_of_size(40))
    stacks_to_process.append(Stack(range(0, total_image_count))) # use all images

    for path in jpeg_paths:
        image = ImageFile(path)
        for stack in stacks_to_process:
            if image.num in stack.img_range:
                stack.add_image(image)

    for stack in stacks_to_process:
        stack.output()
