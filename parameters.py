import math
import numpy as np

from typing import Callable, Dict, List

from pybfsw.gse.parameter import Parameter, ParameterBank
# from pybfsw.payloads.gaps import intf_sensor_cal
# from pybfsw.payloads.gaps.gondola_hardcoding import GAPSMaps
# from pybfsw.payloads.gaps.mppt_alarms import mppt_alarms

# gaps_map = GAPSMaps()

def pdu_power(x):
    return x

def pdu_temp(x):
    voltage = (x * 2.5) / 4096.0
    temp = ((voltage - 0.750) / 0.01) + 25.0
    return temp

def pdu_voltage(x):
    sc = 32.0 / 65536.0
    return x * sc

def pdu_voltage_on_off(x):
    v = pdu_voltage(x)
    if v > 10: return True
    return False

def pdu_vbat(x):
    sc = (1.0 / 16.0) * (1.0 / 1023.0) * 2.5 * 16
    # 1/16 factor since adc accumulates 16 readings
    # scale by ADC FSR 1023
    # multiply by 2.5 vref
    # factor of 16 from resistive divider

    return x * sc

def pdu_current(x):
    sc = 0.1 / (0.005 * 65536.0)
    return sc * x

def pdu_power_acc(x):
    PwrFSR = 3.2 / 0.005  # 3.2V^2 / 0.01 Ohms = 320 Watts (eq 4-5)
    return (x / 2**28) * (
        PwrFSR #/ 1024.0 (used to divide this out in pdu gui, now divide it out here)
    )  # this is an energy, (Watts / sampling rate)

def labjack_lm135(x):
    return (x * 100.0) - 273.15

def bit_select(x, b):
    return (x & (1 << b)) >> b

def bit_select_with_noise(x, b):
    xx = (x & (1 << b)) >> b
    return xx + np.random.uniform(-0.01, 0.01, len(xx))

def divide_by_10k(x):
    return x/10000

def divide_by_100(x):
    return x/100

def divide_by_10(x):
    return x/10

def divide_by_1000(x):
    return x/1000

def times_1000(x):
    return x*1000

def times_8000(x):
    return x*8000

def divide_by_1000_8(x):
    return x*8/1000

def scale_val(x,s):
    return x*float(s)

def switch_bytes(x):
    a, b = divmod(x, 256)
    return  256 * b + a

def low_alt_pressure(x):
    a,b=divmod(x,256)
    return 0.3242*(256*b+a) + 2.1008

def mid_alt_pressure(x):
    return 0.0326*switch_bytes(x) + 0.2041

def high_alt_pressure(x):
    return 0.0033*switch_bytes(x) - 0.006

def make_parameter_bank():

    parameters = []
    p = Parameter(
        f'@lakeshore_temperature',
        'lakeshore',
        'temperature'
    )
    parameters.append(p)

    # # PDU
    # vsense_lists = {}
    # power_lists = {}
    # for pdu_id in gaps_map.pdu_channels:
    #     vsense_lists[pdu_id] = [f'vsense_avg{i}' for i in range(8)]
    #     power_lists[pdu_id] = [f'vpower_acc{i}/acc_count_pac{i//4}' for i in range(8)]
    #     p = Parameter(
    #         f'@pdu{pdu_id}_current',
    #         'pdu_hkp',
    #         ' + '.join(vsense_lists[pdu_id]),
    #         units = 'A',
    #         where = f'pdu_id = {pdu_id}',
    #         converter = pdu_current,
    #     )
    #     parameters.append(p)
    #     p = Parameter(
    #         f'@pdu{pdu_id}_power',
    #         'pdu_hkp',
    #         ' + '.join(power_lists[pdu_id]),
    #         units = 'W',
    #         where = f'pdu_id = {pdu_id}',
    #         converter = pdu_power_acc,
    #     )
    #     parameters.append(p)
    #     p = Parameter(
    #         f"@pdu{pdu_id}_vbat",
    #         "pdu_hkp",
    #         "vbat",
    #         where=f"pdu_id = {pdu_id}",
    #         converter=pdu_vbat,
    #         units="V",
    #         low_range=23.5,
    #         high_range=29.8,
    #         low_alarm=19,#23,
    #         high_alarm=29.9,
    #     )
    #     parameters.append(p)

    #     for ch in range(8):
    #         name = gaps_map.pdu_channels[pdu_id][ch]
    #         if not name in gaps_map.pdu_limits:
    #             for stem in gaps_map.pdu_limits:
    #                 if len(stem) > 0 and len(stem) < len(name) and stem == name[:len(stem)]:
    #                     name = stem
    #             if not name in gaps_map.pdu_limits:
    #                 name = ""
    #         p = Parameter(
    #             f"@vbus_pdu{pdu_id}ch{ch}",
    #             "pdu_hkp",
    #             f"vbus_avg{ch}",
    #             where=f"pdu_id = {pdu_id}",
    #             converter=pdu_voltage,
    #             units="V",
    #             low_range=0,#pdu_voltage_ranges[(pdu_id,ch)][0],
    #             high_range=32,#pdu_voltage_ranges[(pdu_id,ch)][1],
    #             low_alarm=-1,
    #             high_alarm=35,  # NOTE - want to add a physically motivated value here
    #         )
    #         parameters.append(p)
    #         p = Parameter(
    #             f"@vbus_inst_pdu{pdu_id}ch{ch}",
    #             "pdu_hkp",
    #             f"vbus{ch}",
    #             where=f"pdu_id = {pdu_id}",
    #             converter=pdu_voltage,
    #             units="V",
    #         )
    #         parameters.append(p)
    #         p = Parameter(
    #             f"@ibus_pdu{pdu_id}ch{ch}",
    #             "pdu_hkp",
    #             f"vsense_avg{ch}",
    #             where=f"pdu_id = {pdu_id}",
    #             converter=pdu_current,
    #             units="A",
    #             low_range= gaps_map.pdu_limits[name][5],
    #             high_range=gaps_map.pdu_limits[name][6],
    #             low_alarm=gaps_map.pdu_limits[name][4],
    #             high_alarm=gaps_map.pdu_limits[name][7],
    #         )
    #         parameters.append(p)
    #         p = Parameter(
    #             f"@ibus_inst_pdu{pdu_id}ch{ch}",
    #             "pdu_hkp",
    #             f"vsense{ch}",
    #             where=f"pdu_id = {pdu_id}",
    #             converter=pdu_current,
    #             units="A",
    #         )
    #         parameters.append(p)
    #         p = Parameter(
    #             f"@power_pdu{pdu_id}ch{ch}",
    #             "pdu_hkp",
    #             f"vpower{ch}",
    #             where=f"pdu_id = {pdu_id}",
    #             converter=pdu_power,
    #             units="W",
    #         )
    #         parameters.append(p)
    #         p = Parameter(
    #             f"@power_acc_pdu{pdu_id}ch{ch}",
    #             "pdu_hkp",
    #             f"vpower_acc{ch}",
    #             where=f"pdu_id = {pdu_id}",
    #             converter=pdu_power_acc,
    #             units="W",  # need to multiply by count_pac0 or count_pac1 to get the power out
    #             low_range= gaps_map.pdu_limits[name][1], # limits are for after conversion with pac
    #             high_range=gaps_map.pdu_limits[name][2],
    #             low_alarm=gaps_map.pdu_limits[name][0],
    #             high_alarm=gaps_map.pdu_limits[name][3],
    #             scale=f"acc_count_pac{ch//4}",
    #             scale_div = True,
    #         )
    #         parameters.append(p)
    #         p = Parameter(
    #             f"@temp_pdu{pdu_id}ch{ch}",
    #             "pdu_hkp",
    #             f"temp{ch}",
    #             where=f"pdu_id = {pdu_id}",
    #             converter=pdu_temp,
    #             units="\u00b0C",
    #             low_range=-30,
    #             high_range=40,
    #             low_alarm=-38,
    #             high_alarm=50,
    #         )
    #         parameters.append(p)
    #     for hkp_par in [
    #         "gcutime",
    #         "rowid",
    #         "counter",
    #         "pdu_count",
    #         "acc_count_pac0",
    #         "acc_count_pac1",
    #     ]:
    #         p = Parameter(
    #             f"@{hkp_par}_pdu{pdu_id}",
    #             "pdu_hkp",
    #             f"{hkp_par}",
    #             where=f"pdu_id = {pdu_id}",
    #             low_range=0,
    #             high_range=float("inf"),
    #             units="",
    #         )
    #         parameters.append(p)
    #         p = Parameter(
    #             f"@pdu{pdu_id}_{hkp_par}",
    #             "pdu_hkp",
    #             f"{hkp_par}",
    #             where=f"pdu_id = {pdu_id}",
    #             low_range=0,
    #             high_range=float("inf"),
    #             units="",
    #         )
    #         parameters.append(p)
    #     p = Parameter(
    #         f"@pdu{pdu_id}_length",
    #         "pdu_hkp",
    #         "length",
    #         where=f"pdu_id = {pdu_id}",
    #         low_range=218,
    #         high_range=218,
    #         units="",
    #     )
    #     parameters.append(p)
    #     p = Parameter(
    #         f"@pdu{pdu_id}_error",
    #         "pdu_hkp",
    #         "error",
    #         where=f"pdu_id = {pdu_id}",
    #         low_range=0,
    #         high_range=0,
    #         low_alarm=0,
    #         high_alarm=0,
    #         units="",
    #     )
    #     parameters.append(p)
    #     p = Parameter(
    #         f"@pdu{pdu_id}_gsemode",
    #         "pdu_hkp",
    #         "gsemode",
    #         where=f"pdu_id = {pdu_id}",
    #         low_range=1,
    #         high_range=1,
    #         units="",
    #     )
    #     parameters.append(p)
    #     p = Parameter(
    #         f"@length_pdu{pdu_id}",
    #         "pdu_hkp",
    #         "length",
    #         where=f"pdu_id = {pdu_id}",
    #         low_range=218,
    #         high_range=218,
    #         units="",
    #     )
    #     parameters.append(p)
    #     p = Parameter(
    #         f"@error_pdu{pdu_id}",
    #         "pdu_hkp",
    #         "error",
    #         where=f"pdu_id = {pdu_id}",
    #         low_range=0,
    #         high_range=0,
    #         low_alarm=0,
    #         high_alarm=0,
    #         units="",
    #     )
    #     parameters.append(p)
    #     p = Parameter(
    #         f"@gsemode_pdu{pdu_id}",
    #         "pdu_hkp",
    #         "gsemode",
    #         where=f"pdu_id = {pdu_id}",
    #         low_range=1,
    #         high_range=1,
    #         units="",
    #     )
    #     parameters.append(p)
    #     p = Parameter(
    #         f"@vbat_pdu{pdu_id}",
    #         "pdu_hkp",
    #         "vbat",
    #         where=f"pdu_id = {pdu_id}",
    #         converter=pdu_vbat,
    #         units="V",
    #         low_range=23.5,
    #         high_range=29.8,
    #         low_alarm=19,#23,
    #         high_alarm=29.9,
    #     )
    #     parameters.append(p)

    # flight cooling system housekeeping parameters and data

    # # rtd temps
    # for rtd_id in range(1, 65):
    #     rtd_db_temporary = rtd_id - 1
    #     p = Parameter(
    #         f"@cooling_rtd_{rtd_id}",
    #         "cooling",
    #         f"rtd_{rtd_db_temporary}",
    #         units="C",
    #         converter=cooling_rtd,
    #     )
    #     parameters.append(p)

    # # unit-less housekeeping vars
    # for hkp in [
    #     "rowid",
    #     "gsemode",
    #     "gcutime",
    #     "counter",
    #     "length",
    #     "frame_counter",
    #     "status_1",
    #     "status_2",
    #     "rx_byte_num",
    #     "rx_cmd_num",
    #     "last_cmd",
    #     "blob",
    # ]:
    #     p = Parameter(
    #         f"@cooling_{hkp}",
    #         "cooling",
    #         hkp,
    #     )
    #     parameters.append(p)

    # for i, status1_par in enumerate(
    #     ["rh_ctrl", "rh", "rh_switched", "rsv_rtd_switched", "sh1", "sh2", "sh3"]
    # ):
    #     p = Parameter(
    #         f"@cooling_{status1_par}",
    #         "cooling",
    #         "status_1",
    #         converter=cooling_status_functions[i],
    #     )
    #     parameters.append(p)

    # for i, status2_par in enumerate(
    #     [
    #         "cmd_error_checksum",
    #         "cmd_error_timeout",
    #         "cmd_read_start",
    #         "sh_dcdc_48v",
    #         "sh_dcdc_39v",
    #         "sh_dcdc_24v",
    #         "rh_dcdc_24v",
    #         "rh_dcdc_12v",
    #     ]
    # ):
    #     p = Parameter(
    #         f"@cooling_{status2_par}",
    #         "cooling",
    #         "status_2",
    #         converter=cooling_status_functions[i],
    #     )
    #     parameters.append(p)

    # # voltage
    # p = Parameter(
    #     "@cooling_fpga_board_v_in",
    #     "cooling",
    #     "fpga_board_v_in",
    #     converter=cooling_fpga_v,
    #     units="V",
    # )
    # parameters.append(p)

    # # current
    # p = Parameter(
    #     "@cooling_fpga_board_i_in",
    #     "cooling",
    #     "fpga_board_i_in",
    #     converter=cooling_fpga_i,
    #     units="A",
    # )
    # parameters.append(p)

    # # pressure
    # p = Parameter(
    #     "@cooling_fpga_board_p",
    #     "cooling",
    #     "fpga_board_p",
    #     converter=cooling_fpga_p,
    #     units="kPa",
    # )
    # parameters.append(p)


    # ##################  LABJACK ######################
    # for i in range(48, 128):
    #     name = ''
    #     lower_limit = -38
    #     lower_alarm = -32
    #     upper_limit = 60
    #     upper_alarm = 60
    #     if i in gaps_map.labjack['temps']:
    #         name = gaps_map.labjack['temps'][i]
    #         for stem in gaps_map.labjack_limits:
    #             if len(stem) > 0 and len(stem) <= len(name) and stem == name[:len(stem)]:
    #                 lower_limit = gaps_map.labjack_limits[stem][1]
    #                 lower_alarm = gaps_map.labjack_limits[stem][0]
    #                 upper_limit = gaps_map.labjack_limits[stem][2]
    #                 upper_alarm = gaps_map.labjack_limits[stem][3]

    #     p = Parameter(
    #         f"@labjack_temp{i}",
    #         "labjack_hkp",
    #         f"ain{i}",
    #         units="C",
    #         converter=labjack_lm135,
    #         low_alarm=lower_alarm,
    #         low_range=lower_limit,
    #         high_alarm=upper_alarm,
    #         high_range=upper_limit
    #     )
    #     parameters.append(p)

    #     if name == '': continue
    #     name = gaps_map.labjack['temps'][i]
    #     p = Parameter(
    #         f"@labjack_temp_{name}",
    #         "labjack_hkp",
    #         f"ain{i}",
    #         units="C",
    #         converter=labjack_lm135,
    #         low_alarm=lower_alarm,
    #         low_range=lower_limit,
    #         high_alarm=upper_alarm,
    #         high_range=upper_limit
    #     )
    #     parameters.append(p)
    # for i in range(16):
    #     heater_byte = 'fio'
    #     j = i
    #     if i > 7:
    #         heater_byte = 'eio'
    #         j = i - 8
    #     p = Parameter(
    #         f"@labjack_heater{i}",
    #         "labjack_hkp",
    #         heater_byte,
    #         units="bool",
    #         converter=lambda x, b=j: bit_select(x, b),
    #     )
    #     parameters.append(p)
    #     p = Parameter(
    #         f"@labjack_thermostat{i}",
    #         "labjack_settings",
    #         'heater_enabled',
    #         units="bool",
    #         converter=lambda x, b=i: bit_select(x, b),
    #     )
    #     parameters.append(p)
    #     p = Parameter(
    #         f"@labjack_thermostat_high{i}",
    #         "labjack_settings",
    #         f'high_{i}',
    #         units="C",
    #     )
    #     parameters.append(p)
    #     p = Parameter(
    #         f"@labjack_thermostat_low{i}",
    #         "labjack_settings",
    #         f'low_{i}',
    #         units="C",
    #     )
    #     parameters.append(p)
    #     p = Parameter(
    #         f"@labjack_thermostat_sensor{i}",
    #         "labjack_settings",
    #         f'ach_{i}',
    #     )
    #     parameters.append(p)
    #     name = gaps_map.labjack['heaters'][i]
    #     names = [name]
    #     if ' and ' in name: names = names + name.split(" and ")
    #     for name in names:
    #         p = Parameter(
    #             f"@labjack_heater_{name}",
    #             "labjack_hkp",
    #             heater_byte,
    #             units="bool",
    #             converter=lambda x, b=j: bit_select(x, b),
    #         )
    #         parameters.append(p)
    # for i in range(3):
    #     p = Parameter(
    #         f"@pdu_thermostat_high{i}",
    #         "heat_hvlv_settings",
    #         f'high{i}',
    #         units="C",
    #     )
    #     parameters.append(p)
    #     p = Parameter(
    #         f"@pdu_thermostat_low{i}",
    #         "heat_hvlv_settings",
    #         f'low{i}',
    #         units="C",
    #     )
    #     parameters.append(p)
    #     p = Parameter(
    #         f"@pdu_thermostat_sensor{i}",
    #         "heat_hvlv_settings",
    #         f'ain{i}',
    #     )
    #     parameters.append(p)
    # p = Parameter(
    #     f'@pdu_heater2',
    #     'pdu_hkp',
    #     f"vbus_avg3",
    #     where=f"pdu_id = 2",
    #     converter=pdu_voltage_on_off,
    # )
    # parameters.append(p)
    # p = Parameter(
    #     f'@pdu_heater1',
    #     'pdu_hkp',
    #     f"vbus_avg4",
    #     where=f"pdu_id = 3",
    #     converter=pdu_voltage_on_off,
    # )
    # parameters.append(p)
    # p = Parameter(
    #     f'@pdu_heater0',
    #     'pdu_hkp',
    #     f"vbus_avg2",
    #     where=f"pdu_id = 1",
    #     converter=pdu_voltage_on_off,
    # )
    # parameters.append(p)
    # for hkp in ["rowid","gsemode","gcutime","counter","length"]:
    #     p = Parameter(
    #         f"@labjack_{hkp}",
    #         "labjack_hkp",
    #         hkp,
    #     )
    #     parameters.append(p)
    #     p = Parameter(
    #         f"@labjack_thermostat_{hkp}",
    #         "labjack_settings",
    #         hkp,
    #     )
    #     parameters.append(p)
    #     p = Parameter(
    #         f"@pdu_thermostat_{hkp}",
    #         "heat_hvlv_settings",
    #         hkp,
    #     )
    #     parameters.append(p)


    # #### RPI HKP #####
    # column_list = ['counter','length','gcutime','gsemode','rowid']
    # for v in column_list:
    #     p = Parameter(
    #         f'@rpi_{v}',
    #         'rpi_hkp',
    #         v
    #     )
    #     parameters.append(p)

    # p = Parameter(
    #     f"@rpi_version",
    #     "rpi_hkp",
    #     f'version',
    # )
    # parameters.append(p)

    # for ch in range(8):
    #   p = Parameter(
    #       f"@rpi_batt_temp{ch}",
    #       "rpi_hkp",
    #       f'temp{ch}',
    #       units='C',
    #       converter=lambda x:500*x/4096-273.15
    #   )
    #   parameters.append(p)

    # for ch in range(8):
    #   p = Parameter(
    #       f"@rpi_heater_state{ch}",
    #       "rpi_hkp",
    #       f'(heater_state_flags >> {ch} & 0x1)',
    #       converter=lambda x: ["OFF", "ON"][x]
    #   )
    #   parameters.append(p)

    #   p = Parameter(
    #       f"@rpi_heater_control{ch}",
    #       "rpi_hkp",
    #       f'((heater_forced_on_mask >> {ch}) & 0x1)*2 + ((thermostat_enabled_mask >> {ch}) & 0x1)',
    #       converter=lambda x: ["OFF", "THERM ON", "ALWAYS ON", "ERROR"][x]
    #   )
    #   parameters.append(p)


    #   #p = Parameter(
    #   #    f"@rpi_heater_thermostat_en",
    #   #    "rpi_hkp",
    #   #    f'thermostat_enabled_mask',
    #   #    converter=lambda x: bitmask_decode(x, ch, ["DISABLED", "ENABLED"])
    #   #)
    #   #parameters.append(p)

    # for ch in range(8):
    #   p = Parameter(
    #       f"@rpi_thermostat_on_temp{ch}",
    #       "rpi_hkp",
    #       f'thermostat_on_temp{ch}',
    #       units='C',
    #       converter=lambda x: x-128
    #   )
    #   parameters.append(p)

    #   p = Parameter(
    #       f"@rpi_thermostat_off_temp{ch}",
    #       "rpi_hkp",
    #       f'thermostat_off_temp{ch}',
    #       units='C',
    #       converter=lambda x: x-128
    #   )
    #   parameters.append(p)


    # # flight computer hkp
    # tab = 'gcumon_hkp'
    # column_list = zip(['host_id','valid','cpu_total','num_cpus','mem_usage','swap_usage','uptime','counter','length','gcutime','gsemode','rowid'],['','','%','','%','','s','','','','',''])
    # for v, u in column_list:
    #     p = Parameter(
    #         f'@gcumon_{v}',
    #         tab,
    #         v,
    #         units =u,
    #     )
    #     parameters.append(p)
    # for core in range(8):
    #     p = Parameter(
    #         f'@gcumon_cpu_core{core}',
    #         tab,
    #         f'cpu_core{core}',
    #         units='%',
    #         )
    #     parameters.append(p)
    # for t in range(16):
    #     p = Parameter(
    #         f'@gcumon_temp{t}',
    #         tab,
    #         f'temp{t}',
    #         units='C',
    #         )
    #     parameters.append(p)

    # # flight computer gcu hkp 2
    # tab = 'gcumon_add1'
    # column_list = ['gsemode','gcutime','counter','length','rowid','milliseconds','pings']
    # columns_per_disk = ['bytes_free','bytes_used','kbps']
    # columns_per_disk_nice_name = ['free','used','write_rate']
    # columns_per_disk_units = ['GB','GB','kbps']
    # columns_per_disk_converter=[lambda x, s=1e-9 : scale_val(x,s),lambda x,s=1e-9 : scale_val(x,s),None]

    # disks = ['disk_a','disk_b','disk_os']
    # link_status = ['link_status_eth_primary','link_status_eth_secondary','link_status_eth_csbf','ntp_ip','ntp_status','tiu_mux_status','starlink_ip']
    # for vname in column_list + link_status:
    #     p = Parameter(
    #         f'@gcumon2_{vname}',
    #         tab,
    #         vname,
    #         )
    #     parameters.append(p)
    # for d in disks:
    #     for i, column in enumerate(columns_per_disk):
    #         p = Parameter(
    #             f'@gcumon2_{d}_{column}',
    #             tab,
    #             f'{d}_{column}'
    #             )
    #         parameters.append(p)
    #         p = Parameter(
    #             f'@gcumon2_{d}_{columns_per_disk_nice_name[i]}',
    #             tab,
    #             f'{d}_{column}',
    #             units = columns_per_disk_units[i],
    #             converter = columns_per_disk_converter[i],
    #             )
    #         parameters.append(p)
    # p = Parameter(
    #     f'@gcumon2_time_acc',
    #     tab,
    #     'milliseconds',
    #     units = 's',
    #     converter=divide_by_1000,
    # )
    # parameters.append(p)


    # # telemetry decimation settings
    # tab = 'decimation_settings'
    # column_list = ['gsemode','gcutime','counter','length','rowid']
    # for v in column_list:
    #     p = Parameter(
    #         f'@tel_dec_{v}',
    #         tab,
    #         v
    #         )
    #     parameters.append(p)

    # def decicalc(x,ptype):
    #     for s in x.split(' '):
    #         if int(s.split(':')[0]) == ptype:
    #             N = int(s.split(':')[1])
    #             M = int(s.split(':')[2])
    #             if N == 0 or M == 0: return 0
    #             return (N/M)

    #     return (1)

    # for i,n in enumerate(['los','tdrss','pilot','starlink']):
    #     p = Parameter(
    #         f'@tel_dec_{n}',
    #         tab,
    #         n
    #         )
    #     parameters.append(p)
    #     for packet_id in gaps_map.packet_types:
    #         p = Parameter(
    #             f'@tel_dec_{n}{packet_id}',
    #             tab,
    #             n,
    #             converter=lambda x: decicalc(x,packet_id),
    #             )
    #         parameters.append(p)

    # telemetry settings
    # tab = 'telem_settings'
    # column_list = ['gsemode','gcutime','counter','length','rowid']
    # for v in column_list:
    #     p = Parameter(
    #         f'@tel_set_{v}',
    #         tab,
    #         v
    #         )
    #     parameters.append(p)
    # for i,n in enumerate(['los','tdrss','pilot','starlink']):
    #     for item,unit,name in zip(['destination_ip','destination_port','rate_limit_kbps'],['','','kbps'],['dest_ip','dest_port','rate_limit']):
    #         p = Parameter(
    #             f'@tel_set_{n}_{name}',
    #             tab,
    #             f'{n}_{item}',
    #             units = unit
    #             )
    #         parameters.append(p)

    # # telemetry statistics
    # tab = 'telem_statistics'
    # column_list = ['gsemode','gcutime','counter','length','rowid','milliseconds','version','num_bytes_incoming']
    # for v in column_list:
    #     p = Parameter(
    #         f'@tel_stat_{v}',
    #         tab,
    #         v
    #         )
    #     parameters.append(p)
    # p = Parameter(
    #     '@tel_stat_time',
    #     tab,
    #     'milliseconds',
    #     units='ms',
    #     )
    # parameters.append(p)
    # p = Parameter(
    #     '@tel_stat_n_incoming',
    #     tab,
    #     'num_bytes_incoming',
    #     units='B',
    #     )
    # parameters.append(p)
    # for i,n in enumerate(['los','tdrss','pilot','starlink']):
    #     for item in ['num_bytes_sent_total','num_bytes_sent','queue_lo_num_bytes','queue_hi_num_bytes','queue_lo_num_dropped','queue_hi_num_dropped','num_dropped_sendto','num_tokens']:
    #         p = Parameter(
    #             f'@tel_stat_{n}_{item}',
    #             tab,
    #             f'{n}_{item}',
    #             )
    #         parameters.append(p)

    #     p = Parameter(
    #         f'@tel_stat_{n}_total_sent',
    #         tab,
    #         f'{n}_num_bytes_sent_total',
    #         units='GB',
    #         converter=lambda x, s = 1e-9 : scale_val(x,s)
    #         )
    #     parameters.append(p)
    #     p = Parameter(
    #         f'@tel_stat_{n}_queue_hi',
    #         tab,
    #         f'{n}_queue_hi_num_bytes',
    #         units='B'
    #         )
    #     parameters.append(p)
    #     p = Parameter(
    #         f'@tel_stat_{n}_queue_lo',
    #         tab,
    #         f'{n}_queue_lo_num_bytes',
    #         units='B'
    #         )
    #     parameters.append(p)

    #     for item,rate in zip(['num_bytes_sent','queue_lo_num_dropped','queue_hi_num_dropped','num_dropped_sendto','num_tokens'],['rate_bytes_sent','queue_lo_dropped','queue_hi_dropped','dropped_sendto','rate_tokens']):
    #         p = Parameter(
    #             f'@tel_stat_{n}_{rate}',
    #             tab,
    #             f'{n}_{item}',
    #             scale=f"milliseconds",
    #             scale_div = True,
    #             units = 'Hz',
    #             converter = times_1000
    #             )
    #         parameters.append(p)


    ############### SIP #############

    # # sip pressure
    # tab = 'sip_pressure'
    # column_list = ['gsemode','gcutime','counter','length','rowid','sip_id']
    # for item in column_list:
    #     p = Parameter(
    #         f'@sip_pressure_{item}',
    #         tab,
    #         item,
    #         )
    #     parameters.append(p)
    # p = Parameter(
    #     f'@sip_pressure_mks_high',
    #     tab,
    #     "mks_high",
    #     converter=high_alt_pressure,
    #     units = 'mBa',
    #     )
    # parameters.append(p)
    # p = Parameter(
    #     f'@sip_pressure_mks_mid',
    #     tab,
    #     "mks_mid",
    #     converter=mid_alt_pressure,
    #     units = 'mBa'
    #     )
    # parameters.append(p)
    # p = Parameter(
    #     f'@sip_pressure_mks_lo',
    #     tab,
    #     "mks_lo",
    #     converter=low_alt_pressure,
    #     units = 'mBa'
    #     )
    # parameters.append(p)

    # # sip time
    # tab = 'sip_time'
    # column_list =  ['gsemode','gcutime','counter','length','rowid','sip_id','time_of_week','week_number','time_offset','cpu_time']
    # for item in column_list[:6]:
    #     p = Parameter(
    #         f'@{tab}_{item}',
    #         tab,
    #         item,
    #         )
    #     parameters.append(p)
    # for item in column_list[6:]:
    #     p = Parameter(
    #         f'@{tab}_{item}',
    #         tab,
    #         item,
    #         )
    #     parameters.append(p)

    # # sip position
    # tab = 'sip_position'
    # column_list =  ['gsemode','gcutime','counter','length','rowid','sip_id','longitude','latitude','altitude','status1','status2']
    # units = [u'\N{DEGREE SIGN}',u'\N{DEGREE SIGN}','m','','']
    # for item in column_list[:6]:
    #     p = Parameter(
    #         f'@{tab}_{item}',
    #         tab,
    #         item,
    #         )
    #     parameters.append(p)
    # for u,item in zip(units,column_list[6:]):
    #     p = Parameter(
    #         f'@{tab}_{item}',
    #         tab,
    #         item,
    #         units = u
    #         )
    #     parameters.append(p)

    return ParameterBank(par=parameters)
