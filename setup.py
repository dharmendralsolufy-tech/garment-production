from setuptools import find_packages, setup

from garment_production import __version__ as version

setup(
	name="garment_production",
	version=version,
	description="Textile and Garment Production Management System",
	author="Dharmendra",
	author_email="gamingdworld7@gamil.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=[],
)
