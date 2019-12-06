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
    HARDWARE.setup(40)

    ## Switch on computer
    HARDWARE.switchOn()

    ## new create the Operative System Kernel
    # "booteamos" el sistema operativo
    kernel = Kernel()

    # Ahora vamos a intentar ejecutar 3 programas a la vez
    ##################
    # prg1 = Program("prg1.exe", [ASM.CPU(2), ASM.IO(), ASM.CPU(3), ASM.IO(), ASM.CPU(2)])
    # prg2 = Program("prg2.exe", [ASM.CPU(7)])
    # prg3 = Program("prg3.exe", [ASM.CPU(4), ASM.IO(), ASM.CPU(1)])
    prg1= Program("prg1.exe", [ASM.CPU(4),ASM.IO(), ASM.CPU(1)])
    prg2 = Program("prg2.exe", [ASM.CPU(7),ASM.CPU(1)])
    prg3 = Program("prg3.exe", [ASM.CPU(9),ASM.IO(),ASM.CPU(1)])
    kernel.run(prg1,1)
    kernel.run(prg2,3)
    kernel.run(prg3,2)
    
    
    
    
  
    



