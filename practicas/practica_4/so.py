### Reemplazarlo con el so.py de la practica anterior
#!/usr/bin/env python
from hardware import *
import log
from so import *

RUNNING= 'RUNNING'
TERMINATED= 'TERMINATED'
WAITING= 'WAITING'
READY= 'READY'
NEW= 'NEW'

## emulates a compiled program
class Program():
    def __init__(self, name, instructions):
        self._name = name
        self._instructions = self.expand(instructions)

    @property
    def name(self):
        return self._name

    @property
    def instructions(self):
        return self._instructions

    def addInstr(self, instruction):
        self._instructions.append(instruction)

    def expand(self, instructions):
        expanded = []
        for i in instructions:
            if isinstance(i, list):
                ## is a list of instructions
                expanded.extend(i)
            else:
                ## a single instr (a String)
                expanded.append(i)

        ## now test if last instruction is EXIT
        ## if not... add an EXIT as final instruction
        last = expanded[-1]
        if not ASM.isEXIT(last):
            expanded.append(INSTRUCTION_EXIT)

        return expanded

    def __repr__(self):
        return "Program({name}, {instructions})".format(name=self._name, instructions=self._instructions)


## emulates an Input/Output device controller (driver)
class IoDeviceController():
    def __init__(self, device):
        self._device = device
        self._currentPCB = None
        self.waitingQueue= WaitingQueue()

    def runOperation(self,_pcbCorriendo, _instruction):
        _pcbCorriendo.state = WAITING
        pair = {'pcb': _pcbCorriendo, 'instruction': _instruction}
        # si lo manda a la impresora o lo encola.
        # lo encola si la impresora esta ocupada,
        # sino lo manda al device execute
        # idle desocupado 
        if(HARDWARE.ioDevice.is_idle):
            self._device.execute(_instruction)
            self._currentPCB=_pcbCorriendo
        else:
            self.waitingQueue.enqueue(pair)
        
    def getFinishedPCB(self):
        finishedPCB = self._currentPCB
        self._currentPCB = None
        return finishedPCB

    def ejecutarDeWaitingQueue(self):
        if (not self.waitingQueue.isEmpty())  and self._device.is_idle:
            pair = self.waitingQueue.dequeue()
            pcb = pair['pcb']
            instruction = pair['instruction']
            self._currentPCB = pcb
            self._device.execute(instruction)

    def __repr__(self):
        return "IoDeviceController for {} running: {}  in waiting: {}".format(self._device.deviceId, self._currentPCB, self.waitingQueue)
        
## emulates the  Interruptions Handlers
class AbstractInterruptionHandler():
    def __init__(self, kernel):
        self._kernel = kernel
        
    @property
    def kernel(self):
        return self._kernel

    def execute(self, irq):
        log.logger.error("-- EXECUTE MUST BE OVERRIDEN in class {classname}".format(classname=self.__class__.__name__))

class KillInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        log.logger.info(" Program Finished ")     
        procesoCorriendo= self.kernel.pcbTable.pcbCorriendo()
        if (procesoCorriendo != None):
            procesoCorriendo.state= TERMINATED
            self.kernel.dispatcher.save(procesoCorriendo)
            
        # if (not self.kernel.readyQueue.isEmpty()) :
        #     next_Pcb = self.kernel.readyQueue.dequeue()
        #     self.kernel.dispatcher.load(next_Pcb)
        # elif (self.kernel.pcbTable.todosTerminados()):
        #     HARDWARE.switchOff()
        #     log.logger.info("gantt {}" .format(self.kernel.gantt))
        
        if (not self.kernel.scheduler.readyQueue.isEmpty()) :
            next_Pcb = self.kernel.scheduler.nextPcb()
            self.kernel.dispatcher.load(next_Pcb)
        elif (self.kernel.pcbTable.todosTerminados()):
            HARDWARE.switchOff()
            log.logger.info("gantt {}" .format(self.kernel.gantt))
                
# dejar el pcb que terminaste de ejecutar en "Terminated", 
#  y usar el loader para removerlo haciendo un save.
# Para saber que proceso terminó podés usar la PCBTable
#  para obtener el proceso que esté en estado "Running"
   
class IoInInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        operation = irq.parameters
        pcbCorriendo= self.kernel.pcbTable.pcbCorriendo()
        self.kernel.dispatcher.save(pcbCorriendo)
        self.kernel.ioDeviceController.runOperation(pcbCorriendo, operation)
        self.ejecutarEnDispactcher() 

    def ejecutarEnDispactcher(self):
        if (not self.kernel.scheduler.readyQueue.isEmpty()):
            next_Pcb = self.kernel.scheduler.nextPcb()
            log.logger.info("que tengo en el pcb {}". format(next_Pcb))
            self.kernel.dispatcher.load(next_Pcb)

        log.logger.info(self.kernel.ioDeviceController)

class IoOutInterruptionHandler(AbstractInterruptionHandler):

    def execute(self, irq):
        pcb = self.kernel.ioDeviceController.getFinishedPCB()
        self.kernel.scheduler.addPcb(pcb)          
        self.kernel.ioDeviceController.ejecutarDeWaitingQueue()
# si el cpu no esta libre lo encolo en la ready que sino lo mando a ejecutar|
# sino esta running en el pcb table es q esta libre
        # if (not self.kernel.pcbTable.pcbCorriendo()): 
        #     self.kernel.dispatcher.load(pcb)
        # else:
        #     pcb.state= READY 
        #     log.logger.info("estoy encolando{}" .format(pcb))
     
    # si hay alguien en la waitingque, lo saco
    # Lo que hay que hacer es mandar el proceso que está en ese device a la ready queue o
    # al cpu (dependiendo de si el cpu estaba ocupado o no). 
    # Además, si había algún otro proceso en la waiting queue lo manda a ejecutar al device.
# emulates the core of an Operative System

class NewInterruptionHandler(AbstractInterruptionHandler):
    def execute(self, irq):
        programa = irq.parameters["program"]
        prioridad= irq.parameters["priority"]
        base =self.kernel.loader.load(programa)
        log.logger.info("la prioridad al inicio {}".format(prioridad))
        pcb = PCB(programa, base, prioridad)
        self.kernel.pcbTable.add(pcb)
        self.kernel.scheduler.addPcb(pcb)
        log.logger.info(HARDWARE)
        
        #preguntarle al dispacther si puede agregarle o no
        
        # if(self.kernel.pcbTable.pcbCorriendo() == None):
        #     self.kernel.dispatcher.load(pcb)
        # else :
        #     self.kernel.scheduler.addPcb(pcb)
        #     # self.kernel.readyQueue.enqueue(pcb)
        #     pcb.state= READY
      
        # log.logger.info("\n Executing program: {name}".format(name=program.name))
        # log.logger.info("\n Executing pcbTable, estado:{}, pid:{}: , pc: {}, prioridad:{}".format(pcb.state,pcb.baseDir,pcb.pc,pcb.prioridad ))
class Kernel():

    def __init__(self):
        self.loader = Loader()
        self.pcbTable = PCBTable()
        self.dispatcher= Dispatcher()
        self.gantt= Gantt(self)
        # self.scheduler=Fcfc()
        # self.scheduler=PrioridadNoExpropiativo(self)
        self.scheduler=PrioridadExpropiativo(self)
       
            
        ## setup interruption handlers
        killHandler = KillInterruptionHandler(self)
        HARDWARE.interruptVector.register(KILL_INTERRUPTION_TYPE, killHandler)

        ioInHandler = IoInInterruptionHandler(self)
        HARDWARE.interruptVector.register(IO_IN_INTERRUPTION_TYPE, ioInHandler)

        ioOutHandler = IoOutInterruptionHandler(self)
        HARDWARE.interruptVector.register(IO_OUT_INTERRUPTION_TYPE, ioOutHandler)
        
        
        HARDWARE.clock.addSubscriber(self.gantt)
        ## controls the Hardware's I/O Device
        self._ioDeviceController = IoDeviceController(HARDWARE.ioDevice)
        
        newHandler= NewInterruptionHandler(self)
        HARDWARE.interruptVector.register(NEW_INTERRUPTION_TYPE, newHandler)
        
    @property
    def ioDeviceController(self):
        return self._ioDeviceController
    
    def run(self,program,prioridad=1):
        log.logger.info("la prioridad en el run {}". format(prioridad))
        newIRQ= IRQ(NEW_INTERRUPTION_TYPE, {"program": program, "priority": prioridad})
        HARDWARE.interruptVector.handle(newIRQ)     
    
    ## emulates a "system call" for programs executionself.loader.load(program)
    #me lo lleve a newHandler
    # def run(self, program):
    #    
    #     base =self.loader.load(program)
    #     pcb = PCB(program, base)
    #     self.pcbTable.table(pcb)
    #     if(self.pcbTable.pcbCorriendo() == None):
    #         self.dispatcher.load(pcb)
    #     else :
    #         self.readyQueue.enqueue(pcb)
    #         pcb.state= READY
      
    #     log.logger.info("\n Executing program: {name}".format(name=program.name))
    #     log.logger.info("\n Executing pcbTable, estado:{}, pid:{}: , pc: {}".format(pcb.state,pcb.baseDir,pcb.pc ))
    #     log.logger.info(HARDWARE)
       
# pc al cpu o deadyQueue?
        # set CPU program counter at program's first intruction
     
        
        # armo pcb y le paso a pcb table el pcb

    def run_batch(self,batch):
        for i in batch:
            self.run(i)
    
    def __repr__(self):
        return "Kernel "

class Loader():
    def __init__(self) :
        self.baseDir_Proximo = 0
    
    def load(self, program) :
        progSize = len(program.instructions)
        for prog in range(0, progSize):
            inst = program.instructions[prog]
            HARDWARE.memory.write(prog + self.baseDir_Proximo, inst)
        self.baseDir_Proximo += progSize
        # retorna la basedir en donde va a comenzar le siguiente programa
        return (self.baseDir_Proximo - progSize)          
class PCB():   
    def __init__(self,program,base,prioridad) :
        self.pid= 0 
        self.pc = 0
        self.state = NEW
        self.baseDir = base
        self.path= program.name  
        self.prioridad = prioridad
        
    def __repr__(self) :
        return "pid {} state {} pc {} path {} basedir{} prioridad {}".format(self.pid, self.state, self.pc, self.path, self.baseDir,self.prioridad)   
    
    # def setPrioridad(self,_prioridad):
    #     self.prioridad=_prioridad   
class PCBTable() :
    def __init__(self) :
        self._pid = 0
        self.pcbs = { }

    def __repr__(self) :
        return tabulate(enumerate(self.pcbs), tablefmt='psql')
             
    def add(self, pcb):
        log.logger.info("la prioridad del pcb en el new:  {}".format(pcb))
        _pidNuevo=self._pid
        self.pcbs[_pidNuevo] = pcb
        pcb.pid = _pidNuevo
        self._pid +=1 
                   
    def pcbCorriendo(self):
        for k,v in self.pcbs.items():
            if(v.state == RUNNING):
                return v 
        return None
    
    def todosTerminados(self):
        for k,v in self.pcbs.items():
            if(v.state != TERMINATED):
                return False
        return True        
    
class Dispatcher() :
    def load (self,pcb):
        log.logger.info("loading dispatcher {} ".format(pcb))
        HARDWARE.cpu.pc = pcb.pc
        HARDWARE.mmu.baseDir= pcb.baseDir        
        pcb.state= RUNNING
        
    def save(self,pcb) :
        log.logger.info("saving {} ".format(pcb))
        pcb.pc= HARDWARE.cpu.pc
        HARDWARE.cpu.pc = -1
        #    # sino queda ninguno vuelve a -1, y sino incrementa
        
class ReadyQueue():
    def __init__(self):
        self.pcbs= []
   
    def enqueue(self, pcb):
        pcb.state= READY
        self.pcbs.append(pcb)
        
    def dequeue (self):
        return self.pcbs.pop(0)
        
    def isEmpty(self):
        return len(self.pcbs ) == 0
class Gantt():
        
    def __init__(self,kernel):
        self._ticks = []
        self._kernel = kernel
   
    def tick (self,tickNbr):
        log.logger.info("guardando información de los estados de los PCBs en el tick N {}".format(tickNbr))
        pcbYEstado = dict()
        pcbTable = self._kernel.pcbTable.pcbs
        for pid,pcb in pcbTable.items():
            pcbYEstado[pid] = pcb.state
        self._ticks.append(pcbYEstado)
  
    def __repr__(self):
        return tabulate(enumerate(self._ticks), tablefmt='grid')
    
class WaitingQueue():
    def __init__(self):
        self.pcbsWaiting= []

    def enqueue(self, pcb):
        self.pcbsWaiting.append(pcb)
    
    def dequeue (self):
        return  self.pcbsWaiting.pop(0)

    def isEmpty(self):
        return len(self.pcbsWaiting ) == 0
    
class AbstractScheduler():
    def __init__(self,_kernel):
        self.readyQueue=ReadyQueue()
        self.kernel=_kernel
    
    def addPcb(self,pcb):
        pass
        
    def nextPcb(self):    
        return self.readyQueue.dequeue()
        
    def mustExpropiet(self):    
        pass
        
class Fcfc(AbstractScheduler):
    def addPcb(self,pcb):
        log.logger.info("la prioridad del pcb es : {}".format(pcb.prioridad))
        log.logger.info("la prioridad despues de cambiarla al  pcb es : {}".format(pcb.prioridad))
        self.readyQueue.enqueue(pcb)
class PrioridadNoExpropiativo(AbstractScheduler):
        
    def addPcb(self,pcb):
        if(self.kernel.pcbTable.pcbCorriendo() == None):
            self.kernel.dispatcher.load(pcb)
        else :
            pcb.state= READY
            log.logger.info("la prioridad del pcb es en Prio : {}".format(pcb.prioridad))
            i = 0
            # sacar la clase readyQueue y poner todo lo q estaba adentro del scheduler
            while(i < len(self.readyQueue.pcbs)  and (self.readyQueue.pcbs[i].prioridad < pcb.prioridad)):
                i = i + 1        
            self.readyQueue.pcbs.insert(i,pcb)
        
class PrioridadExpropiativo(AbstractScheduler):
    def addPcb(self,pcb):
        if(self.kernel.pcbTable.pcbCorriendo() == None):
            self.kernel.dispatcher.load(pcb)
        else :
            pcbCorriendo=self.kernel.pcbTable.pcbCorriendo()
            
            if(pcb.prioridad < pcbCorriendo.prioridad):
                self.kernel.dispatcher.save(pcbCorriendo)
                log.logger.info("hola estoy adentro del if{}" .format(pcbCorriendo))
            # # tengo q sacar el q esta en el dispacher preguntarle la prioridad, si es menor a la mia no vuelvo a meter
            # # a meter en la readyQue, sino lo agrego a la readyQue por prioridad.
                pcbCorriendo.state= READY
                log.logger.info("la prioridad del pcb es en Prio : {}".format(pcbCorriendo))
                i = 0
            # sacar la clase readyQueue y poner todo lo q estaba adentro del scheduler
                while(i < len(self.readyQueue.pcbs)  and (self.readyQueue.pcbs[i].prioridad < pcbCorriendo.prioridad)):
                    i = i + 1        
                self.readyQueue.pcbs.insert(i,pcbCorriendo)
                self.kernel.dispatcher.load(pcb)
            else:
                pcb.state= READY
                log.logger.info("la prioridad del pcb es en Prio : {}".format(pcb))
                i = 0
            # sacar la clase readyQueue y poner todo lo q estaba adentro del scheduler
                while(i < len(self.readyQueue.pcbs)  and (self.readyQueue.pcbs[i].prioridad < pcb.prioridad)):
                    i = i + 1        
                self.readyQueue.pcbs.insert(i,pcb)
        
            
        
        
            
        
        
        

    
    
    
    
    
    
    
        
        

    
    
    
    
    
    
    