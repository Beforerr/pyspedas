import cdflib
import numpy as np

from copy import deepcopy
from pytplot import get_data, store_data, options, clip, ylim

from ...satellite.erg.load import load


def gmag_isee_induction(
    trange=["2018-10-18/00:00:00", "2018-10-18/02:00:00"],
    suffix="",
    site="all",
    get_support_data=False,
    varformat=None,
    varnames=[],
    downloadonly=False,
    notplot=False,
    no_update=False,
    uname=None,
    passwd=None,
    time_clip=False,
    ror=True,
    frequency_dependent=False,
):
    """
    Load data from ISEE Induction Magnetometers

    Parameters
    ----------
    trange: list of str
            time range of interest [starttime, endtime] with the format
            'YYYY-MM-DD','YYYY-MM-DD'] or to specify more or less than a day
            ['YYYY-MM-DD/hh:mm:ss','YYYY-MM-DD/hh:mm:ss']
            Default: ['2018-10-18/00:00:00', '2018-10-18/02:00:00']

    suffix: str
            The tplot variable names will be given this suffix.  Default: ''

    site: str or list of str
            The site or list of sites to load. Valid values: "ath", "gak", "hus", "kap", "lcl", "mgd", "msr",
            "nai", "ptk", "rik", "sta", "zgn", "all"
            Default: ['all']

    get_support_data: bool
            If true, data with an attribute "VAR_TYPE" with a value of "support_data"
            or 'data' will be loaded into tplot. Default: False

    varformat: str
            The CDF file variable formats to load into tplot.  Wildcard character
            "*" is accepted.  Default: None (all variables will be loaded).

    varnames: list of str
            List of variable names to load. Default: [] (all variables will be loaded)

    downloadonly: bool
            Set this flag to download the CDF files, but not load them into
            tplot variables. Default: False

    notplot: bool
            Return the data in hash tables instead of creating tplot variables. Default: False

    no_update: bool
            If set, only load data from your local cache. Default: False

    uname: str
            User name.  Default: None

    passwd: str
            Password. Default: None

    time_clip: bool
            Time clip the variables to exactly the range specified in the trange keyword. Default: False

    ror: bool
            If set, print PI info and rules of the road. Default: True

    frequency_dependent: bool
            If set, load frequency dependent data.
            Default: False

    Returns
    -------

    Examples
    ________

    >>> import pyspedas
    >>> from pytplot import tplot
    >>> ind_vars=pyspedas.erg.gmag_isee_induction(trange=['2020-08-01','2020-08-02'], site='all')
    >>> tplot('isee_induction_db_dt_msr')
    """

    site_code_all = [
        "ath",
        "gak",
        "hus",
        "kap",
        "lcl",
        "mgd",
        "msr",
        "nai",
        "ptk",
        "rik",
        "sta",
        "zgn",
    ]

    if isinstance(site, str):
        site_code = site.lower()
        site_code = site_code.split(" ")
    elif isinstance(site, list):
        site_code = []
        for i in range(len(site)):
            site_code.append(site[i].lower())
    if "all" in site_code:
        site_code = site_code_all

    site_code = list(set(site_code).intersection(site_code_all))

    if frequency_dependent:
        frequency_dependent_structure = {}
        for site_input in site_code:
            frequency_dependent_structure[site_input] = {
                "site_code": "",
                "nfreq": 0,
                "frequency": np.zeros(shape=(64)),
                "sensitivity": np.zeros(shape=(64, 3)),
                "phase_difference": np.zeros(shape=(64, 3)),
            }

    prefix = "isee_induction_"
    if notplot:
        loaded_data = {}
    else:
        loaded_data = []

    for site_input in site_code:
        file_res = 3600.0
        pathformat = (
            "ground/geomag/isee/induction/"
            + site_input
            + "/%Y/%m/isee_induction_"
            + site_input
            + "_%Y%m%d%H_v??.cdf"
        )

        loaded_data_temp = load(
            pathformat=pathformat,
            file_res=file_res,
            trange=trange,
            prefix=prefix,
            suffix="_" + site_input + suffix,
            get_support_data=get_support_data,
            varformat=varformat,
            downloadonly=downloadonly,
            notplot=notplot,
            time_clip=time_clip,
            no_update=no_update,
            uname=uname,
            passwd=passwd,
        )

        if notplot:
            loaded_data.update(loaded_data_temp)
        else:
            loaded_data += loaded_data_temp
        if (len(loaded_data_temp) > 0) and ror:
            try:
                if isinstance(loaded_data_temp, list):
                    if downloadonly:
                        cdf_file = cdflib.CDF(loaded_data_temp[-1])
                        gatt = cdf_file.globalattsget()
                    else:
                        gatt = get_data(loaded_data_temp[-1], metadata=True)["CDF"][
                            "GATT"
                        ]
                elif isinstance(loaded_data_temp, dict):
                    gatt = loaded_data_temp[list(loaded_data_temp.keys())[-1]]["CDF"][
                        "GATT"
                    ]
                print(
                    "**************************************************************************"
                )
                print(gatt["Logical_source_description"])
                print("")
                print(f'Information about {gatt["Station_code"]}')
                print("PI and Host PI(s):")
                print(gatt["PI_name"])
                print("")
                print("Affiliation: ")
                print(gatt["PI_affiliation"])
                print("")
                print("Rules of the Road for ISEE Induction Magnetometer Data Use:")
                for gatt_text in gatt["TEXT"]:
                    print(gatt_text)
                print(gatt["LINK_TEXT"])
                print(
                    "**************************************************************************"
                )
            except:
                print("printing PI info and rules of the road was failed")

        if (not downloadonly) and (not notplot):
            tplot_name = prefix + "db_dt_" + site_input + suffix
            if tplot_name in loaded_data:
                clip(tplot_name, -1e4, 1e4)
                get_data_vars = get_data(tplot_name)
                ylim(
                    tplot_name, np.nanmin(get_data_vars[1]), np.nanmax(get_data_vars[1])
                )
                options(tplot_name, "legend_names", ["dH/dt", "dD/dt", "dZ/dt"])
                options(tplot_name, "Color", ["b", "g", "r"])
                options(tplot_name, "ytitle", "\n".join(tplot_name.split("_")))

                if frequency_dependent:
                    meta_data_var = get_data(tplot_name, metadata=True)

                    if meta_data_var is not None:
                        cdf_file = cdflib.CDF(meta_data_var["CDF"]["FILENAME"])
                        cdfcont = cdf_file.varget("frequency", inq=True)
                        ffreq = cdf_file.varget("frequency")
                        ssensi = cdf_file.varget("sensitivity")
                        pphase = cdf_file.varget("phase_difference")
                        frequency_dependent_structure[site_input][
                            "site_code"
                        ] = site_input
                        frequency_dependent_structure[site_input]["nfreq"] = (
                            cdfcont["max_records"] + 1
                        )
                        frequency_dependent_structure[site_input]["frequency"][
                            0 : ffreq.shape[0]
                        ] = deepcopy(ffreq)
                        frequency_dependent_structure[site_input]["sensitivity"][
                            0 : ssensi.shape[0]
                        ] = deepcopy(ssensi)
                        frequency_dependent_structure[site_input]["phase_difference"][
                            0 : pphase.shape[0]
                        ] = deepcopy(pphase)

    if frequency_dependent:
        return frequency_dependent_structure
    else:
        return loaded_data
