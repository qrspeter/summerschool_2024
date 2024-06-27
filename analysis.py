# analysis.py
# Принимает в качестве аргумента командной строки имя файла, сформированного скриптом laser.py (например, "python analysis.py measurement_data.csv")
# Выводит график зависимости фотоотклика проводимости (до и после каждой накачки) от дозы облучения.

import numpy as np
import matplotlib.pyplot as plt
from measurement import var
import sys

# цикл для создания двух списков откликов - до накачки и после
def resp(all_laser_data, probe_positions):
    constant = 10
    resp = []
    dark = []
    for i in probe_positions:
        for j in all_laser_data[1:]:
            t_segm = all_laser_data[0][i[0] - constant : i[1] + constant]
            d_segm = j[i[0] - constant : i[1] + constant]
            element = np.vstack((t_segm, d_segm))
            r, d = responce_calc_dc(element, i[0], i[1]-i[0])
            resp.append(r)
            dark.append(d)
            
    return resp, dark
        
# Расчет величины отклика на зондирующий импульс
# Возвращает отклик и величину темнового тока на начало отклика
def responce_calc_dc(drift, probe_begin, duration):
    appr_deg=1
    approx_length = duration    
    probe_duration = duration  
    
    begin = np.searchsorted(drift[0], probe_begin)
    end = np.searchsorted(drift[0], probe_begin + duration)
    

    slice_before = drift[:, :begin]
    slice_after = drift[:, end:]

    appr_before = np.polyfit(slice_before[0], slice_before[1], deg=appr_deg)
    appr_after = np.polyfit(slice_after[0], slice_after[1], deg=appr_deg)
    
    
    calc_pos = drift[0, end]
    responce = np.polyval(appr_after, calc_pos) - np.polyval(appr_before, calc_pos)
    if False:      
        plt.plot(drift[0], drift[1], label='data')
        plt.plot(slice_before[0], np.polyval(appr_before, slice_before[0]), label='before')
        plt.plot(slice_after[0], np.polyval(appr_after, slice_after[0]), label='after')
        plt.xlabel('Time, s')
        plt.ylabel('Current, A')
        plt.legend() # (loc='upper left')
        plt.show()
        
    return (responce, np.polyval(appr_before, slice_before[0, -1]))
    

filename = sys.argv[1]
all_laser_data = np.loadtxt(filename, delimiter=',')

pump_start = var.pump_start
pump_duration = var.pump_duration
probe_shift = var.probe_shift
probe_duration = var.probe_duration
dose = var.dose 

probe_positions = ((pump_start - probe_shift, pump_start - probe_shift + probe_duration), (pump_start + pump_duration + probe_shift, pump_start + pump_duration + probe_shift + probe_duration))


resp, dark = resp(all_laser_data.T, probe_positions)

doses = [i*dose  for i in range(len(resp)//2)]

plt.plot(doses, resp[:len(resp)//2], 'ro', label='before')
plt.plot(doses, resp[len(resp)//2:], 'g*', label='after')

y1 = resp[:len(resp)//2]
begin = 1
poly1 = np.polyfit(doses[begin:], y1[begin:], deg=1)
plt.plot(doses[begin:], np.polyval(poly1, doses[begin:]), color='red', label='aprox_before', linestyle='dashed')
y2 = resp[len(resp)//2:]
poly2 = np.polyfit(doses, y2, deg=1)
plt.plot(doses, np.polyval(poly2, doses), color='green', label='aprox_after', linestyle='dashed')
plt.xlabel('Dose, J/cm$^2$', fontsize=14) #
plt.ylabel('Photocurrent $\delta$I, A', fontsize=14)
plt.title('Photocurrent vs Dose after pumps', fontsize=14)
plt.legend()
plt.show()
