# point-collocation

A helper package for doing lat/lon/time matchups using `earthaccess` and NASA EarthData products.

## Documentation

Full documentation is available at: **<https://fish-pace.github.io/point-collocation/>**

- [Installation](https://fish-pace.github.io/point-collocation/installation/)
- [Quickstart](https://fish-pace.github.io/point-collocation/quickstart/)
- [API Reference](https://fish-pace.github.io/point-collocation/api/)

Examples are included for PACE, TEMPO, ICESat-2 ATL21, ECCO and MUR.

## PyPI

<https://pypi.org/project/point-collocation/>

## Data Regions

This package currently is designed to do point matchups against NASA EarthData. In a virtual machine in AWS us-west-2, where NASA cloud data is, the point matchups are fast. In Colab, say, your comppute is not in the same data region nor provider (Google versus AWS), and the same matchups might take 10x longer. Thus if you have big matchup tasks, 10s of thousands of points, it is wise to do that in AWS us-west-2.