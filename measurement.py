# measurement.py
# Записывает ток через образец при периодическом воздействии накачки и зондирующих импульсов (в циклах).
# Формирует файл с таблицей, соответствующей циклам, и файл с непрерывной записью данных в одну колонку.


from KeithleyV15 import SMU26xx
import time
import datetime
import csv
import winsound
import numpy as np
import time
import matplotlib.pyplot as plt

sampleName = 'NPl_CdSe_p2_24W'
currentRange = 1e-4

class Variables:
    inputVoltage = 2.0 
    interval = 1
    dose = 24
    
    warmup_duration = 200 # sec, Delay for warm-up
    periods = 6
    period = 2000
    pump_duration = 200
    pump_start = 100
    pump_level = 1

    probe_duration = 2
    probe_shift = 50 # before and after pump probe
    probe_level = 1
    

var = Variables()


def single_measurement(voltage, average=1):
    # or replace one
    # [current, voltage] = drain.measure_current_and_voltage()
    # return current, voltage

    current_accum = 0.0
    drain.set_voltage(voltage)
    for i in range(average):
        [current, voltage] = drain.measure_current_and_voltage()
        current_accum += current
    drain.set_voltage(0)        
    return current_accum/average, voltage


def warm_up(duration, filenameRaw):
    sm.write_lua("digio.writebit(1, 0)")
    times = []
    arr_graph = []
    plt.ion()  # enable interactivity
    fig = plt.figure()  # make a figure
    ax = fig.add_subplot(111)
    line1, = ax.plot(times, arr_graph, 'r.')
    line1.set_xdata(times)
    line1.set_ydata(arr_graph)
    plt.xlabel('Time / s', fontsize=14)
    plt.ylabel('Current / A', fontsize=14)
    plt.title(f'Warm-up up to {duration} sec', fontsize=14)
    plt.tick_params(labelsize = 14)

    times = []
    arr_graph = []
    startTime = time.time()
    nowTime = time.time()
    print('Warm-up started. Press Ctl+C to start measurement')
    while nowTime - startTime < var.pump_duration:
        position = var.interval * len(times)
        while nowTime - startTime < position:
            nowTime = time.time()

        #[current, voltage] = drain.measure_current_and_voltage()
        [current, voltage] = single_measurement(var.inputVoltage)
        print('%.4f' % (nowTime - startTime), '%.5e' % current, '%.2f' % voltage)
        with open(filenameRaw, 'a') as csvfile:
            writer = csv.writer(csvfile,  lineterminator='\n')
            nt = time.time()
            writer.writerow(['%.3f' % (nt - start_meas), current, voltage])
        
        times.append(nowTime - startTime)
        arr_graph.append(current)

        line1.set_xdata(times)
        line1.set_ydata(arr_graph)
        ax.relim()
        ax.autoscale()
        fig.canvas.draw()
        #plt.pause(0.001)
        fig.canvas.flush_events()
        nowTime = time.time()
    plt.ioff()
    plt.close()        
    

def acquisition(start_meas, arr, filenameRaw):
    startTime = time.time()
    nowTime = time.time()
    laserState = 0
    sm.write_lua("digio.writebit(1, 0)")
    times = []
    arr_graph = []
    plt.ion()  # enable interactivity
    fig = plt.figure()  # make a figure
    ax = fig.add_subplot(111)
    line1, = ax.plot(times, arr_graph, 'r.')
    line1.set_xdata(times)
    line1.set_ydata(arr_graph)
    plt.xlabel('Time / s', fontsize=14)
    plt.ylabel('Current / A', fontsize=14)
    plt.title(time_for_title, fontsize=14)
    plt.tick_params(labelsize = 14)
    
    for i in range(arr.size):
        position = var.interval * i
        while nowTime - startTime < position:
            nowTime = time.time()
            
        if (position >= var.pump_start) and (position < var.pump_start + var.pump_duration): 
            laserState = 10
            #sm.write_lua("digio.writebit(1, {})".format(laserState))
        elif ((position >= var.pump_start - var.probe_shift) and (position < var.pump_start - var.probe_shift + var.probe_duration)) \
            or ((position >= var.pump_start + var.pump_duration + var.probe_shift) and (position < var.pump_start + var.pump_duration + var.probe_shift + var.probe_duration)):            
            laserState = 1
            #sm.write_lua("digio.writebit(1, {})".format(laserState))
        else:
            laserState = 0
            #sm.write_lua("digio.writebit(1, {})".format(laserState))
        sm.write_lua("digio.writebit(1, {})".format(laserState))
            
        
        #[current, voltage] = drain.measure_current_and_voltage()
        [current, voltage] = single_measurement(var.inputVoltage)
        print('%.4f' % (nowTime - startTime), '%.5e' % current, '%.2f' % voltage, 'laserState=', laserState)
        with open(filenameRaw, 'a') as csvfile:
            writer = csv.writer(csvfile,  lineterminator='\n')
            nt = time.time()
            writer.writerow(['%.3f' % (nt - start_meas), current, voltage])
        
        arr[i] = current
        times.append(nowTime - startTime)
        arr_graph.append(current)

        line1.set_xdata(times)
        line1.set_ydata(arr_graph)
        ax.relim()
        ax.autoscale()
        fig.canvas.draw()
        #plt.pause(0.001)
        fig.canvas.flush_events()
    plt.ioff()
    plt.close()
    sm.write_lua("digio.writebit(1, 0)")

def lists2file(columnNames, defFilename, defLst):
    delim = ','
    columnNames_str = delim.join(columnNames)
    
    np_data = np.stack(defLst, axis=0)

    np.savetxt(defFilename, np_data.T, fmt='%.10g', delimiter=delim, header=columnNames_str) 

    
def data2fig(defLst, columnNames, defFilename, show=False, savefig=True):
    
    np_arr = np.stack(defLst, axis=0)
    fig = plt.figure(figsize=(8,6))
    for i in range(np_arr.shape[0]-1):
        plt.plot(np_arr[0, :], np_arr[i+1,:], label=columnNames[i + 1], linewidth=2)
    plt.xlabel('Time (s)', fontsize=14)
    plt.ylabel('Current (A)', fontsize=14)
    plt.title(time_for_title, fontsize=14)
    plt.tick_params(labelsize = 14)
    plt.legend(loc='upper left')
    if savefig == True:
        plt.savefig(defFilename)
    if show == True:
        plt.show()
        
if __name__ == "__main__":
    
    """ ******* Connect to the Sourcemeter ******** """

    # initialize the Sourcemeter and connect to it
    # for USB connection
    sm = SMU26xx('USB0::0x05E6::0x2636::4097970::INSTR') 
    # or for TCP connection:
    # sm = SMU26xx(TCPIP0::192.166.1.101::INSTR)

    # get one channel of the Sourcemeter 
    drain = sm.get_channel(sm.CHANNEL_A)


    # reset to default settings
    drain.reset()
    # setup the operation mode of the source meter to act as a voltage source - the SMU generates a voltage and measures the current
    drain.set_mode_voltage_source()

    # set the voltage and current parameters
    max_voltage = 40
    drain.set_voltage_range(max_voltage)
    drain.set_voltage_limit(max_voltage)
    drain.set_voltage(0)
    drain.set_current_range(currentRange)
    drain.set_current_limit(currentRange)
    drain.set_current(0)

    drain.set_measurement_speed_hi_accuracy()
    # or faster, but less precious
    # drain.set_measurement_speed_normal()
    """ ******* For saving the data ******** """

    # Create unique filenames for saving the data
    time_for_name = datetime.datetime.now().strftime("%Y_%m_%d_%H%M%S")
    time_for_title = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    filename_av = './data/' + 'PhotoCond_' + time_for_name + '_'  + sampleName + '_vds_' + str(var.inputVoltage) +  '_cycles_' + str(var.periods) + '.csv'
    filenameRaw = './data/' + 'PhotoCond_' + time_for_name + '_'  + sampleName + 'Raw' + '.csv'
    filename = './data/' + 'PhotoCond_' + time_for_name + '_'  + sampleName + '.csv'

    """ ******* Do some measurements ******** """

    # enable the output
    drain.enable_output()

    # switch the laser off
    sm.write_lua("digio.writebit(1, 0)")

    #drain.set_voltage(var.inputVoltage)
    drain.set_voltage(0)

    assert var.period > var.pump_duration + var.pump_start, "Check timing parameters - var.period, var.pump_duration and pump_delay"

    periodLength = int(var.period / var.interval)
    timestamp = var.interval * np.array(range(periodLength))

    columnNames = []
    lst = []
    columnNames.append("Time, s")
    lst.append(timestamp)
        
    data_acq = np.zeros(periodLength)

    with open(filenameRaw, 'a') as csvfile:
        writer = csv.writer(csvfile,  lineterminator='\n')
        writer.writerow(['Time, s' , 'Current, A', 'Voltage, V'])

    start_meas = time.time()
    warm_up(var.warmup_duration, filenameRaw)

    try:    
        print('Measurement started. Press Ctl+C to escape')
        for i in range(var.periods):
            acquisition(start_meas, data_acq, filenameRaw)
            lst.append(data_acq.copy())
            columnNames.append(f'{i+1}')

            print('Cycle ', i + 1, ' from ', var.periods)
            lists2file(columnNames, filename, lst)
            
    except KeyboardInterrupt:
        sm.write_lua("digio.writebit(1,0)")

            
    winsound.Beep(1000, 300)

    data2fig(lst, columnNames, filenameRaw[:-4] + '.png', show=True, savefig=True)
