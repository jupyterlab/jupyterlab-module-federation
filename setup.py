


from setuptools import setup


setup(name='jupyterlab-module-federation',
      version='0.1.0',
      py_modules = ['main'],
      install_requires=[
        'jupyterlab==3.0.0a8',
        'jupyterlab_server==2.0.0a4'
    ],
    extras_require={
        'test': ['pytest', 'coverage']
    },
)
