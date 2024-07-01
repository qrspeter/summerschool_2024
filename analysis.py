# analysis.py
# Принимает в качестве аргумента командной строки имя файла, сформированного скриптом laser.py (например, "python analysis.py measurement_data.csv")
# Выводит график зависимости фотоотклика проводимости (до и после каждой накачки) от дозы облучения.

import numpy as np
import matplotlib.pyplot as plt
from measurement import var
import sys
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score

# цикл для создания двух списков откликов - до накачки и после
def calculate_responces(it_data, probe_positions):
    approximated_range = 10
    resp = []
    dark = []
    for i in probe_positions:
        for j in it_data[1:]:
            t_segm = it_data[0][i[0] - approximated_range : i[1] + approximated_range]
            d_segm = j[i[0] - approximated_range : i[1] + approximated_range]
            element = np.vstack((t_segm, d_segm))
            r, d = responce_calc(element, i[0], i[1]-i[0])
            resp.append(r)
            dark.append(d)
            
    return resp, dark
        
# Расчет величины отклика на зондирующий импульс
# Возвращает отклик и величину темнового тока на начало отклика
# it_slice is a list [[t data], [I data]] with one probe only
def responce_calc(it_slice, probe_begin, duration, plot=False):
    appr_deg=1
    approx_length = duration    
    probe_duration = duration  
    
    begin = np.searchsorted(it_slice[0], probe_begin)
    end = np.searchsorted(it_slice[0], probe_begin + duration)
    

    slice_before = it_slice[:, :begin]
    slice_after = it_slice[:, end:]

    appr_before = np.polyfit(slice_before[0], slice_before[1], deg=appr_deg)
    appr_after = np.polyfit(slice_after[0], slice_after[1], deg=appr_deg)
    
    
    calc_pos = it_slice[0, end]
    responce = np.polyval(appr_after, calc_pos) - np.polyval(appr_before, calc_pos)
    dark_current = np.polyval(appr_before, slice_before[0, -1])
    if plot == True:      
        plt.plot(it_slice[0], it_slice[1], label='data')
        plt.plot(slice_before[0], np.polyval(appr_before, slice_before[0]), label='before')
        plt.plot(slice_after[0], np.polyval(appr_after, slice_after[0]), label='after')
        plt.xlabel('Time, s')
        plt.ylabel('Current, A')
        plt.legend() # (loc='upper left')
        plt.show()
        
    return (responce, dark_current)
    

# creating list of decay times
def calculate_decays(it_data, pump_position, pump_duration):
    pump_end = pump_position + pump_duration
    begin = np.searchsorted(it_data[0], pump_end)
    end = len(it_data[0])//2
    t_segm = it_data[0][begin:end]
    decays = []
    for j in it_data[1:]:
        i_segm = j[begin:end]
        decay = exp_decay(t_segm, i_segm)
        decays.append(decay)
            
    return decays

# calculating decay time on segment
def exp_decay(x, y, plot=False):
    func = lambda x,a1,t1, b: a1*np.exp(t1*x) + b
    p0 = (0.5, -1/500, 0.5) # the initial guess for the second parameter is 500 sec

    y /=np.max(y)
    popt, pcov = curve_fit(func,  x, y, p0=p0) # popt is [a. b]
    y_pred = func(x, *popt)

    time = -1/popt[1]
    
    err = r2_score(x, y_pred)
    print(f'Parameters: {popt[0]=:g}, {popt[1]=:g}, {err=:g}')
    print(f'Time: {time}')

    if plot == True:      
        plt.plot(x, y, linewidth=2, label='data')
        plt.plot(x, y_pred, linewidth=1, label=r'$\tau$=' + f'{time:.3g}')  # *popt is [a. b]

        plt.xlabel('Times, s')
        plt.ylabel('Intensity, a.u.')
        plt.legend() #(loc='upper left')
        plt.title('Approximation by exponential function')
        plt.show()
    return time    

filename = sys.argv[1]
it_array = np.loadtxt(filename, delimiter=',')

pump_start = var.pump_start
pump_duration = var.pump_duration
probe_shift = var.probe_shift
probe_duration = var.probe_duration
dose = var.dose 

probe_positions = ((pump_start - probe_shift, pump_start - probe_shift + probe_duration), (pump_start + pump_duration + probe_shift, pump_start + pump_duration + probe_shift + probe_duration))


data = []
resp, dark = calculate_responces(it_array.T, probe_positions)

doses = [(i + 1)*dose  for i in range(len(resp)//2)]

data.append(doses)
resp_before = resp[:len(resp)//2]
resp_after  = resp[len(resp)//2:]
dark_before = dark[:len(dark)//2]
dark_after  = dark[len(dark)//2:]

data.append(resp_before)
data.append(resp_after)
data.append(dark_before)
data.append(dark_after)

np_arr = np.array(data)

np.savetxt(filename[:-4] + '_calc.csv', np_arr.T, fmt='%.6e', header = 'Dose, resp_before, resp_after, dark_before, dark_after', delimiter=',')


if True:
    plt.plot(doses, resp[:len(resp)//2], 'ro', label='before')
    plt.plot(doses, resp[len(resp)//2:], 'g*', label='after')


    begin = 1
    poly_before = np.polyfit(doses[begin:], resp_before[begin:], deg=1)
    plt.plot(doses[begin:], np.polyval(poly_before, doses[begin:]), color='red', label='aprox_before', linestyle='dashed')
    begin = 1
    poly_after = np.polyfit(doses[begin:], resp_after[begin:], deg=1)
    plt.plot(doses[begin:], np.polyval(poly_after, doses[begin:]), color='green', label='aprox_after', linestyle='dashed')
    plt.xlabel('Dose, J/cm$^2$', fontsize=14) #
    plt.ylabel('Photocurrent $\delta$I, A', fontsize=14)
    plt.title('Photocurrent vs Dose after pumps', fontsize=14)
    plt.legend()
    plt.show()


    plt.plot(doses, dark[:len(dark)//2], 'ro', label='before')
    plt.plot(doses, dark[len(dark)//2:], 'g*', label='after')

    begin = 1
    poly_before = np.polyfit(doses[begin:], dark_before[begin:], deg=1)
    plt.plot(doses[begin:], np.polyval(poly_before, doses[begin:]), color='red', label='aprox_before', linestyle='dashed')
    begin = 1
    poly_after = np.polyfit(doses[begin:], dark_after[begin:], deg=1)
    plt.plot(doses[begin:], np.polyval(poly_after, doses[begin:]), color='green', label='aprox_after', linestyle='dashed')
    plt.xlabel('Dose, J/cm$^2$', fontsize=14) #
    plt.ylabel('Dark current, A', fontsize=14)
    plt.title('Dark current vs Dose after pumps', fontsize=14)
    plt.legend()
    plt.show()

# ===========================
# decays calculation
# ===========================

pump_position = var.pump_start
pump_duration = var.pump_duration
decays = []

decays.append(doses)
decays.append(calculate_decays(it_array.T, pump_position, pump_duration))
print(f'{decays=}')
np_decays = np.array(decays)

np.savetxt(filename[:-4] + '_decays.csv', np_decays.T, fmt='%.6e', header = 'Dose, decays', delimiter=',')



if True:
    plt.plot(doses, decays[1], 'ro', label=r'$\tau$')
    #plt.plot(doses, decays[1], 'ro', label=f'$\tau$')
    begin = 0
    poly = np.polyfit(doses[begin:], decays[1][begin:], deg=1)
    plt.plot(doses[begin:], np.polyval(poly, doses[begin:]), color='red', label='aprox', linestyle='dashed')
    plt.xlabel('Dose, J/cm$^2$', fontsize=14) #
    plt.ylabel('Decay time, s', fontsize=14)
    plt.title('Decay time vs Dose after pumps', fontsize=14)
    plt.legend()
    plt.show() 