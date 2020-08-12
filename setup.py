


from setuptools import setup


setup(name='jupyterlab-module-federation',
      version='0.1.0',
      py_modules = ['main'],
      install_requires=[
        'jupyterlab==3.0.0a9',
        'jupyterlab_server==2.0.0b0'
    ],
    extras_require={
        'test': ['pytest', 'coverage']
    },
)
