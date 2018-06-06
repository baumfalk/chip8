SKIP_INSTRUCTION = 4

from random import randint
import math
import time

class Chip8EMU(object):
    def __init__(self, filename, debug=False):
        self.debug = debug
        bytes = list(self.bytes_from_file(filename))
        self.memory = [0b0] * int(0x1000)
        self.delay = 0
        self.time_delay_set=0

        self.sound = 0
        self.time_sound_set = 0
        self.createSpritesMemory()
        self.sprite_addr = list(range(0,80,5))


        curIndex = 0x200
        for i in range(len(bytes)):
            self.memory[curIndex] = bytes[i]
            curIndex += 1
        self.V = [0b0] * 16 # 16 registers, V0 t/m VF
        self.I = 0b0 #16 bits
        self.stack = []
        self.PC = 0x200
        self.keysDown = [0b0]*16
        self.screen = [[0 for i in range(64)] for j in range(32)] #screenbits

    def createSpritesMemory(self):
        # add numbers
        # 0
        self.memory[0:5] = [0xF0, 0x90, 0x90, 0x90, 0xF0]
        # 1
        self.memory[5:10] = [0x20, 0x60, 0x20, 0x20, 0x70]
        # 2
        self.memory[10:15] = [0xF0, 0x10, 0xF0, 0x80, 0xF0]
        # 3
        self.memory[15:20] = [0xF0, 0x10, 0xF0, 0x10, 0xF0]
        # 4
        self.memory[20:25] = [0x90, 0x90, 0xF0, 0x10, 0x10]
        # 5
        self.memory[25:30] = [0xF0, 0x80, 0xF0, 0x10, 0xF0]
        # 6
        self.memory[30:35] = [0xF0, 0x80, 0xF0, 0x90, 0xF0]
        # 7
        self.memory[35:40] = [0xF0, 0x10, 0x20, 0x40, 0x40]
        # 8
        self.memory[40:45] = [0xF0, 0x90, 0xF0, 0x90, 0xF0]
        # 9
        self.memory[45:50] = [0xF0, 0x90, 0xF0, 0x10, 0xF0]
        # A
        self.memory[50:55] = [0xF0, 0x90, 0xF0, 0x90, 0x90]
        # B
        self.memory[55:60] = [0xE0, 0x90, 0xE0, 0x90, 0xE0]
        # C
        self.memory[60:65] = [0xF0, 0x80, 0x80, 0x80, 0xF0]
        # D
        self.memory[65:70] = [0xE0, 0x90, 0x90, 0x90, 0xE0]
        # E
        self.memory[70:75] = [0xF0, 0x80, 0xF0, 0x80, 0xF0]
        # F
        self.memory[75:80] = [0xF0, 0x80, 0xF0, 0x80, 0x80]

    def bytes_from_file(self, filename, chunksize=8192):
        with open(filename, "rb") as f:
            while True:
                chunk = f.read(chunksize)
                if chunk:
                    for b in chunk:
                        yield b
                else:
                    break

    def parseBytes(self, bytes):
        for i in range(0, len(bytes), 2):
            self.printInstruction(bytes[i], bytes[i+1], i)

    def printInstruction(self, byte1, byte2, i):
        instruction = self.parseBytePair(byte1, byte2)
        if(instruction != "NOOP"):
            print(format(i, '05x').upper(), str(format(byte1, '02x')), str(format(byte2, '02x')), instruction)

    def parseBytePair(self, firstBytePair, secondBytePair):
        fBL, fBR = self.splitBytePair(firstBytePair)
        sBL, sbR = self.splitBytePair(secondBytePair)
        rightPart = (fBR << 8) + secondBytePair
        if fBL == 0x0:
            if rightPart == 0x000:
                return "NOOP"
            elif fBR == 0x0 and secondBytePair == 0xE0:
                return "CLEAR"
            elif fBR == 0x0 and secondBytePair == 0xEE:
                return "RETURN"
            return "Not implemented yet"
        elif fBL == 0x1:
            return "GOTO " + self.f(rightPart)
        elif fBL == 0x2:
            return "CALL " + self.f(rightPart)
        elif fBL == 0x3:
            return "COND.EQ V" + self.f(fBR) + " , 0x" + self.f(secondBytePair)
        elif fBL == 0x4:
            return "COND.NEQ V" + self.f(fBR) + " , 0x" + self.f(secondBytePair)
        elif fBL == 0x5:
            return "COND.VX V" + self.f(fBR) + " , V" + self.f(sBL)
        elif fBL == 0x6:
            return "MOV V" + self.f(fBR) + " , 0x" + self.f(secondBytePair)
        elif fBL == 0x7:
            return "ADD V" + self.f(fBR) + " , 0x" + self.f(secondBytePair)
        elif fBL == 0x8:
            if sbR == 0x0:
                return "SET V" + self.f(fBR) + " , V" + self.f(sBL)
            elif sbR == 0x1:
                return "SET.OR V" + self.f(fBR) + " , V" + self.f(sBL)
            elif sbR == 0x2:
                return "SET.AND V" + self.f(fBR) + " , V" + self.f(sBL)
            elif sbR == 0x3:
                return "SET.XOR V" + self.f(fBR) + " , V" + self.f(sBL)
            elif sbR == 0x4:
                return "ADD.V V" + self.f(fBR) + " , V" + self.f(sBL)
            elif sbR == 0x5:
                return "SUB.V V" + self.f(fBR) + " , V" + self.f(sBL)
            elif sbR == 0x6:
                return "SHIFTR.V V" + self.f(fBR) + " , V" + self.f(sBL)
            elif sbR == 0x7:
                return "SUB.V2 V" + self.f(fBR) + " , V" + self.f(sBL)
            elif sbR == 0xE:
                return "SHIFTL.V V" + self.f(fBR) + " , V" + self.f(sBL)
            return "Not implemented yet"
        elif fBL == 0x9:
            return "COND.NEQV V" + self.f(fBR) + " , V" + self.f(sBL)
        elif fBL == 0xA:
            return "SET.I 0x" + self.f(rightPart)
        elif fBL == 0xB:
            return "GOTO.V0 " + self.f(rightPart)
        elif fBL == 0xC:
            return "RAND.V V" + self.f(fBR) + " , 0x" + self.f(secondBytePair)
        elif fBL == 0xD:
            return "DRAW V" + self.f(fBR) + " , V" + self.f(sBL) + " , 0x" + self.f(sbR)
        elif fBL == 0xE:
            if secondBytePair == 0x9E:
                return "KEYPRESS V" + self.f(fBR)
            elif secondBytePair == 0xA1:
                return "KEYNOTPRESS V" + self.f(fBR)
            return "Not implemented yet"
        elif fBL == 0xF:
            if secondBytePair == 0x07:
                return "GETDELAY V" + self.f(fBR)
            elif secondBytePair == 0x0A:
                return "GETKEY V" + self.f(fBR)
            elif secondBytePair == 0x15:
                return "DELAY V" + self.f(fBR)
            elif secondBytePair == 0x18:
                return "SOUND V" + self.f(fBR)
            elif secondBytePair == 0x1E:
                return "ADD.I V" + self.f(fBR)
            elif secondBytePair == 0x29:
                return "SPRITE.I V" + self.f(fBR)
            elif secondBytePair == 0x33:
                return "BCD.I V" + self.f(fBR)
            elif secondBytePair == 0x55:
                return "DUMP.I V" + self.f(fBR)
            elif secondBytePair == 0x65:
                return "READ.I V" + self.f(fBR)
            return "Not implemented yet"
        else:
            return "Not implemented yet"

    def f(self, firstByteRight):
        return str(format(firstByteRight, '01x')).upper()

    def splitBytePair(self, bytePair):
        leftByte = bytePair >> 4
        rightByte = bytePair ^ (leftByte << 4)
        return leftByte, rightByte

    def run(self):
        pass

    def execNextInstruction(self):
        oldPC = self.PC
        firstBytePair = self.memory[self.PC]
        secondBytePair = self.memory[self.PC + 1]
        response = self.executeInstruction(firstBytePair, secondBytePair)
        #print(format(oldPC, '05x').upper(), str(format(firstBytePair, '02x')), str(format(secondBytePair, '02x')), response)
        if oldPC == self.PC: #no jump was made, execute next instruction
            self.PC += 2

        return response

    def executeInstruction(self, firstBytePair, secondBytePair):
        fBL, fBR = self.splitBytePair(firstBytePair)
        sBL, sbR = self.splitBytePair(secondBytePair)
        rightPart = (fBR << 8) + secondBytePair
        #self.printInstruction(firstBytePair, secondBytePair, self.PC)
        if fBL == 0x0:
            if rightPart == 0x000:
                return "NOOP"
            elif fBR == 0x0 and secondBytePair == 0xE0:
                self.screen = [[0 for i in range(64)] for j in range(32)]  # reset screen
                return "CLEAR"
            elif fBR == 0x0 and secondBytePair == 0xEE:
                self.PC = self.stack.pop() + 2
                return "RETURN"
            return "Not implemented yet"
        elif fBL == 0x1:
            return self.GOTO(rightPart)
        elif fBL == 0x2:
            return self.CALL(rightPart)
        elif fBL == 0x3:
            return self.COND_EQV(fBR, secondBytePair)
        elif fBL == 0x4:
            return self.COND_NEQV(fBR, secondBytePair)
        elif fBL == 0x5:
            return self.COND_VX(fBR, sBL)
        elif fBL == 0x6:
            return self.MOV(fBR, secondBytePair)
        elif fBL == 0x7:
            return self.ADD(fBR, secondBytePair)
        elif fBL == 0x8:
            if sbR == 0x0:
                return self.SET_V(fBR, sBL)
            elif sbR == 0x1:
                return self.SET_OR_V(fBR, sBL)
            elif sbR == 0x2:
                return self.SET_AND_V(fBR, sBL)
            elif sbR == 0x3:
                return self.SET_XOR_V(fBR, sBL)
            elif sbR == 0x4:
                return self.ADD_V(fBR, sBL)
            elif sbR == 0x5:
                return self.SUB_V(fBR, sBL)
            elif sbR == 0x6:
                return self.SHIFTR(fBR, sBL)
            elif sbR == 0x7:
                return self.SUB_V2(fBR, sBL)
            elif sbR == 0xE:
                return self.SHIFTL(fBR, sBL)
            return "Not implemented yet"
        elif fBL == 0x9:
            return self.COND_NEQV2(fBR, sBL)
        elif fBL == 0xA:
            return self.SET_I(rightPart)
        elif fBL == 0xB:
            return self.GOTO_V0(rightPart)
        elif fBL == 0xC:
            return self.RAND_V(fBR, secondBytePair)
        elif fBL == 0xD:
            return self.DRAW(fBR, sBL, sbR)
        elif fBL == 0xE:
            if secondBytePair == 0x9E:
                return "KEYPRESS V" + self.f(fBR)
            elif secondBytePair == 0xA1:
                return "KEYNOTPRESS V" + self.f(fBR)
            return "Not implemented yet"
        elif fBL == 0xF:
            if secondBytePair == 0x07:
                curTime = time.time()
                numberOfTicks = math.floor((curTime - self.time_delay_set) * 120)
                curDelayValue = max(0, self.delay - numberOfTicks)
                self.V[fBR] = curDelayValue
                #print("curDELAY:", self.V[fBR], self.delay, numberOfTicks)
                return "GETDELAY V" + self.f(fBR)
            elif secondBytePair == 0x0A:
                return "GETKEY V" + self.f(fBR)
            elif secondBytePair == 0x15:
                self.delay = self.V[fBR]
                self.time_delay_set = time.time()
                return "DELAY V" + self.f(fBR)
            elif secondBytePair == 0x18:
                return "SOUND V" + self.f(fBR)
            elif secondBytePair == 0x1E:
                return "ADD.I V" + self.f(fBR)
            elif secondBytePair == 0x29:
                spr = self.V[fBR]

                self.I = self.sprite_addr[spr]
                return "SPRITE.I V" + self.f(fBR) + " (" + str(spr) + ")"
            elif secondBytePair == 0x33:
                return self.BCD_I(fBR)
            elif secondBytePair == 0x55:
                return "DUMP.I V" + self.f(fBR)
            elif secondBytePair == 0x65:
                return self.READ_I(fBR)
            return "Not implemented yet"
        else:
            return "Not implemented yet"

    def READ_I(self, fBR):
        for i in range(fBR + 1):

            self.V[i] = self.memory[self.I]
            self.I += 1
        return "READ.I V" + self.f(fBR)

    def BCD_I(self, fBR):
        num = self.V[fBR]
        hundreds = int(num / 100)
        tens = int(num / 10) % 10
        singles = num % 10

        self.memory[self.I] = hundreds
        self.memory[self.I + 1] = tens
        self.memory[self.I + 2] = singles
        return "BCD.I V" + self.f(fBR)

    def DRAW(self, fBR, sBL, sbR):
        bytesToPrint = self.memory[self.I:(self.I + sbR)]
        startX = self.V[fBR]
        startY = self.V[sBL]

        for curByteIndex in range(len(bytesToPrint)):
            curByte = bytesToPrint[curByteIndex]
            curY = (startY + curByteIndex) % 32

            for i in range(8):
                curX = (startX + i) % 64
                whichBitToPrint = 7 - i
                newPixel = 1 & (curByte >> whichBitToPrint)

                if not self.V[0xF] and self.screen[curY][curX] and newPixel:
                    self.V[0xF] = 1
                self.screen[curY][curX] = self.screen[curY][curX] ^ newPixel
        return "DRAW V" + self.f(fBR) + " , V" + self.f(sBL) + " , 0x" + self.f(sbR)

    def RAND_V(self, fBR, secondBytePair):
        rNum = randint(0, 255)
        self.V[fBR] = rNum & secondBytePair
        return "RAND.V V" + self.f(fBR) + " , 0x" + self.f(secondBytePair)

    def GOTO_V0(self, rightPart):
        self.PC = self.V[0] + rightPart
        return "GOTO.V0 " + self.f(rightPart)

    def SET_I(self, rightPart):
        self.I = rightPart
        return "SET.I 0x" + self.f(rightPart)

    def COND_NEQV2(self, fBR, sBL):
        if self.V[fBR] != self.V[sBL]:
            self.PC += SKIP_INSTRUCTION  # skip next instruction
        return "COND.NEQV V" + self.f(fBR) + " , V" + self.f(sBL)

    def SHIFTL(self, fBR, sBL):
        msb = self.V[sBL] & 0x80  # 128, most significant bit
        self.V[0xF] = msb
        self.V[sBL] << 1
        self.V[sBL] = self.V[sBL] & 0xff
        self.V[fBR] = self.V[sBL]
        return "SHIFTL.V V" + self.f(fBR) + " , V" + self.f(sBL)

    def SUB_V2(self, fBR, sBL):
        self.V[fBR] = self.V[sBL] - self.V[fBR]
        self.V[0xF] = 1 if self.V[fBR] < 0 else 0  # V[F] = 1 iff borrow
        self.V[fBR] & 0xff  # underflow
        return "SUB.V2 V" + self.f(fBR) + " , V" + self.f(sBL)

    def SHIFTR(self, fBR, sBL):
        lsb = self.V[sBL] & 0b1
        self.V[0xF] = lsb
        self.V[fBR] = self.V[sBL] >> 1
        return "SHIFTR.V V" + self.f(fBR) + " , V" + self.f(sBL)

    def SUB_V(self, fBR, sBL):
        self.V[fBR] -= self.V[sBL]
        self.V[0xF] = 1 if self.V[fBR] < 0 else 0  # V[F] = 1 iff borrow
        self.V[fBR] & 0xff  # underflow
        return "SUB.V V" + self.f(fBR) + " , V" + self.f(sBL)

    def ADD_V(self, fBR, sBL):
        self.V[fBR] += self.V[sBL]
        self.V[0xF] = 1 if self.V[fBR] > 0xff else 0  # V[F] = 1 iff carry
        self.V[fBR] & 0xff  # overflow
        return "ADD.V V" + self.f(fBR) + " , V" + self.f(sBL)

    def SET_XOR_V(self, fBR, sBL):
        self.V[fBR] = self.V[fBR] ^ self.V[sBL]
        return "SET.XOR V" + self.f(fBR) + " , V" + self.f(sBL)

    def SET_AND_V(self, fBR, sBL):
        self.V[fBR] = self.V[fBR] & self.V[sBL]
        return "SET.AND V" + self.f(fBR) + " , V" + self.f(sBL)

    def SET_OR_V(self, fBR, sBL):
        self.V[fBR] = self.V[fBR] | self.V[sBL]
        return "SET.OR V" + self.f(fBR) + " , V" + self.f(sBL)

    def SET_V(self, fBR, sBL):
        self.V[fBR] = self.V[sBL]
        return "SET V" + self.f(fBR) + " , V" + self.f(sBL)

    def ADD(self, fBR, secondBytePair):
        self.V[fBR] += secondBytePair & 0xff  # overflow: 255 + 1 = 0
        return "ADD V" + self.f(fBR) + " , 0x" + self.f(secondBytePair)

    def MOV(self, fBR, secondBytePair):
        self.V[fBR] = secondBytePair
        return "MOV V" + self.f(fBR) + " , 0x" + self.f(secondBytePair)

    def COND_VX(self, fBR, sBL):
        if self.V[fBR] == self.V[sBL]:
            self.PC += SKIP_INSTRUCTION  # skip next instruction
        return "COND.VX V" + self.f(fBR) + " , V" + self.f(sBL)

    def COND_NEQV(self, fBR, secondBytePair):
        if self.V[fBR] != secondBytePair:
            self.PC += SKIP_INSTRUCTION  # skip next instruction
        return "COND.NEQ V" + self.f(fBR) + " , 0x" + self.f(secondBytePair)

    def COND_EQV(self, fBR, secondBytePair):
        if self.V[fBR] == secondBytePair:
            self.PC += SKIP_INSTRUCTION  # skip next instruction
        return "COND.EQ V" + self.f(fBR) + " , 0x" + self.f(secondBytePair)

    def CALL(self, rightPart):
        self.stack.append(self.PC)
        self.PC = rightPart
        return "CALL " + self.f(rightPart)

    def GOTO(self, rightPart):
        self.PC = rightPart
        return "GOTO " + self.f(rightPart)

    def keyPressed(self, hexNum):
        if hexNum == 1:
            return

    def logState(self):
        print()
        print("STATE")
        print("------")
        for i in range(16):
            print("V[" + self.f(i) +"] = 0x" + self.f(self.V[i]))
        print()
        print("I =", self.f(self.I))
        print("PC =", self.f(self.PC))
        print("STACK = ", self.stack)
        print()

    def run(self):
        if self.debug:
            self.logState()
        while self.PC < len(self.memory) - 1:
            resp = self.execNextInstruction()
            if self.debug:
                print(resp)
                self.logState()
    def runNextStep(self):
        if self.debug:
            self.logState()
        if self.PC < len(self.memory) - 1:
            resp = self.execNextInstruction()
            if self.debug:
                print(resp)
                self.logState()

if __name__ == '__main__':
    d = Chip8EMU('roms/test.dms', debug=False)
    d.parseBytes(d.memory)
    #output = d.run()
