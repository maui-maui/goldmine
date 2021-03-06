from setuptools import setup, find_packages
import re, os

requirements = []
with open('requirements.txt') as f:
    requirements = [i.replace('\n', '').replace('\r', '') for i in f.readlines()]
    requirements.remove('https://github.com/Armored-Dragon/discord.py/archive/master.zip#egg=discord.py')

version = ''
with open('__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('Version is not set')

readme = ''
with open('README.md') as f:
    readme = f.read()

extras_require = {
    'full': ['plyvel', 'uvloop', 'cchardet', 'discord.py[voice]>=0.15.1', 'python-rapidjson']
}

dep_links = [
    'https://github.com/Armored-Dragon/discord.py/archive/master.zip#egg=discord.py',
    'https://github.com/Armored-Dragon/discord.py/archive/master.zip#egg=discord.py[voice]'
]

setup(name='goldmine',
      author='Dragon5232',
      url='https://github.com/Armored-Dragon/goldmine',
      version=version,
      packages=find_packages(),
      license='MIT',
      description='A new bot for Discord that keeps things nice and snug.',
      long_description=readme,
      include_package_data=True,
      dependency_links=dep_links,
      install_requires=requirements,
      extras_require=extras_require,
      classifiers=[
          'Development Status :: 4 - Beta',
          'License :: OSI Approved :: MIT License',
          'Intended Audience :: Developers',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Topic :: Internet',
          'Topic :: Software Development :: Libraries',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: Utilities',
      ]
)
