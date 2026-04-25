from setuptools import setup, Extension
import pybind11

pybind11_includes = pybind11.get_include()

ext_modules = [
    Extension(
        'pieces',
        ['pieces.cpp'],
        include_dirs=[pybind11_includes],
        libraries=['user32', 'gdi32'],
        language='c++',
        extra_compile_args=['/std:c++17'],
    ),
    Extension(
        'invert',
        ['invert.cpp'],
        include_dirs=[pybind11_includes],
        libraries=['user32', 'gdi32'],
        language='c++',
        extra_compile_args=['/std:c++17'],
    ),
]

setup(
    name='death_extensions',
    version='1.0',
    ext_modules=ext_modules,
    requires=['pybind11'],
)
