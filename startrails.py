#!/usr/bin/env python3
import os
import numpy
import argparse
import math


from PIL import Image


def get_subset_of_files(files : list, start_filename : str = None, end_filename : str = None) -> list:
    if start_filename == None and end_filename == None:
        return files
    start_index = 0
    end_index = len(files)
    if start_filename:
        start_index = files.index(start_filename)
    if end_filename:    
        end_index = files.index(end_filename)
    # both can throw ValueError
    return files[start_index:end_index]


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
file_paths = [ args.target_dir + x for x in file_paths ]
jpeg_paths = list(filter(lambda x: x.endswith(".JPG"), file_paths))

if args.skip_num:
    jpeg_paths = jpeg_paths[::args.skip_num]

total_image_count = len(jpeg_paths)

import os
import psutil
process = psutil.Process(os.getpid())

class ImageFile():
    IMAGE_COUNTER = 0

    def __init__(self, file_path):
        self.path = file_path
        #self.filename = ""
        image = Image.open(self.path)
        self.array = numpy.array(image, dtype = numpy.float)
        self.size = image.size
#        print(process.memory_percent())  # for debugging memory usage, not very useful w/ Mac's kernel_task

        ImageFile.IMAGE_COUNTER += 1
        self.num = ImageFile.IMAGE_COUNTER
        print("loaded image {}/{}: '{}'".format(self.num, total_image_count, self.path))

    def __del__(self):
        print("deleted image {}/{}".format(self.num, total_image_count))



# batch loading & processing, to make best use of memory
# preload first image :)
first_image = ImageFile(jpeg_paths.pop(0))
width, height = first_image.size

images = []
images.append(first_image)

batch_size = 15 # seems like a reasonable limit for my 8GB physical mem mac mini 2012
                # because I'm dealing w/ images of 4000x6000px size as numpy arrays. (could preload and use nbytes for size estimate)

class Stack():
    def __init__(self, img_range, width, height):
        self.img_range = img_range
        self.array = numpy.zeros((height, width, 3), numpy.float)

    def add_image(self, image):
        self.array = numpy.maximum(self.array, image.array)
        print("image {}, added to stack {}".format(image.num, self.img_range))

    def output(self):
        new_stack = numpy.array(numpy.round(self.array), dtype = numpy.uint8)
        output = Image.fromarray(new_stack, mode = "RGB")
        filename = "stack_{}-{}.jpeg".format(self.img_range.start, self.img_range.stop)
        output.save(filename, "JPEG")
        print("Saved stack to {}".format(filename))


stack_subset_size = 20
stacks = math.floor(total_image_count/stack_subset_size)
print("stacks " + str(stacks))
stack_subsets = []
for i in range(0, stacks):
    stk = Stack(range(i * stack_subset_size, i * stack_subset_size + stack_subset_size), width, height)
    stack_subsets.append(stk)

batches = math.ceil(total_image_count / batch_size)
for b in range(0, batches):
    print("processing batch {}/{}".format(b, batches))
    batch_start_index = (b * batch_size)
    batch_end_index = min((b * batch_size + batch_size), total_image_count - 1)

    # load batch
    for i, path in enumerate(jpeg_paths[batch_start_index:batch_end_index]):
        image = ImageFile(path)
        if (width, height) != image.size:  # ensure sizes are consistent.
            raise Exception("{} != {}".format(image.size, (width, height)))  #TODO include filename w/ exception
        images.append(image)

    # process batch, w/ stack definitions
    for i, stack in enumerate(stack_subsets):
        for image in images:
            if image.num in stack.img_range:
                stack.add_image(image)

    # clear images batch cache, to free memory for each image.array
    images.clear()

# write stacked images to disk :)
for i, stack in enumerate(stack_subsets):
    stack.output()
