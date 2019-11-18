from hardware import *
from so import *
import log


##
##  MAIN 
##
if __name__ == '__main__':
    log.setupLogger()
    log.logger.info('Starting emulator')

    ## setup our hardware and set memory size to 25 "cells"
    HARDWARE.setup(25)

    ## Switch on computer
    HARDWARE.switchOn()

    ## new create the Operative System Kernel
    # "booteamos" el sistema operativo
    kernel = Kernel()

    ##  create a program
    
    prg1= Program("prg1.exe", [ASM.CPU(1), ASM.IO(),ASM.CPU(1)])
    prg2 = Program("prg2.exe", [ASM.CPU(2),ASM.IO(),ASM.CPU(2)])
    prg = Program("test.exe", [ASM.CPU(2), ASM.CPU(3), ASM.CPU(3)])
    prg3 = Program("prg3.exe", [ASM.CPU(2),ASM.CPU(1),])
    
    batch=[prg1,prg2]
    # execute the program
    ##kernel.run(prg)
    kernel.run_batch(batch)
    # execute the program
    # kernel.run(prg)





