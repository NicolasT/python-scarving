from PIL import Image, ImageOps
import numpy

class EnergyCalculator:
        def __init__(self, image):
                self._energy = None
                
                if isinstance(image, numpy.ndarray):
                        self._image = image.copy()
                        return

                # Assume this is a PIL Image
                # TODO: How to recognize this?
                (w, h) = image.size
                self._image = numpy.reshape(ImageOps.grayscale(image).getdata(), (h, w))

        def calculate_per_pixel(self):
                raise NotImplemented

        def _calculate_pixel_energy(self, x, y):
                if self.calculate_per_pixel() == False:
                        raise Exception, "This function should not be called when calculate_per_pixel is False"
                raise NotImplemented

        def _calculate_full_energy(self):
                if self.calculate_per_pixel() == True:
                        raise Exception, "This function should not be called when calculate_per_pixel is True"
                raise NotImplemented

        def calculate(self):
                if self.calculate_per_pixel() == False:
                        e = self._calculate_full_energy()
                        if not isinstance(e, numpy.ndarray):
                                raise Exception, "Return value of _calculate_full_energy should be of type numpy.ndarray"
                        self._energy = e
                else:
                        h = len(self._image)
                        if h < 1:
                                raise Exception, "Invalid image size"
                        w = len(self._image[0])
                        for y in range(0, h):
                                for x in range(0, w):
                                        e = self._calculate_pixel_energy(x, y)
                                        if not isinstance(e, int):
                                                raise Exception, "Return value of _calculate_pixel_energy should be of type int"
                                        e = clamp(e)
                                        self._energy[y, x] = e

        def get_image_matrix(self):
                return self._image.copy()

        def get_image_pixel(self, x, y):
                return self._image[y, x]

        def get_energy_matrix(self):
                if self._energy == None:
                        self.calculate()
                return self._energy.copy()

        def get_energy(self, x, y):
                if self._energy == None:
                        self.calculate()
                return self._energy[y, x]

        def get_energy_image(self):
                if self._energy == None:
                        self.calculate()
                h = len(self._energy)
                if h < 1:
                        raise Exception, "Energy matrix too small"
                w = len(self._energy[0])
                im = Image.new("L", (w, h))
                im.putdata(list(self._energy.flat))
                return im
