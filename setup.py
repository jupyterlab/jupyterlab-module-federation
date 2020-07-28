


from setuptools import setup


setup(name='jupyterlab-module-federation',
      version='0.1.0',
      py_modules = ['main'],
      install_requires=[
        'jupyterlab'
    ],
    extras_require={
        'test': ['pytest', 'coverage']
    },
)
