#!/usr/bin/env python3
import os
import numpy
from PIL import Image

#target_dir = "/Users/mitchell/Pictures/Photography/2019/Australia/Astro1/Astro/"
target_dir = "/Users/Mitchell/Pictures/2019/Australia/Astro1/Astro/"

start_filename = "DSCF7579.JPG"
end_filename = "DSCF7675.JPG"

file_paths = os.listdir(target_dir)
file_paths.sort()
file_paths = file_paths[file_paths.index(start_filename):file_paths.index(end_filename)]
file_paths = [ target_dir + x for x in file_paths ]

jpeg_paths = list(filter(lambda x: x.endswith(".JPG"), file_paths))
jpeg_paths.sort()
total_image_count = len(jpeg_paths)

width, height = Image.open(jpeg_paths[0]).size

stack = numpy.zeros((height, width, 3), numpy.float)
counter = 1

for i, image in enumerate(jpeg_paths):
    print("Processing image {}/{}: '{}'".format(i, total_image_count, image))
    image_new = numpy.array(Image.open(image), dtype = numpy.float)
    stack = numpy.maximum(stack, image_new)
    counter += 1

stack = numpy.array(numpy.round(stack), dtype = numpy.uint8)

output = Image.fromarray(stack, mode = "RGB")
output_filename = "trail-test.jpg"
output.save(output_filename, "JPEG")
print("Stacked image saved to: {}".format(output_filename))
