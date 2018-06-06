SKIP_INSTRUCTION = 4

from random import randint
import math
class Dissassembler(object):
    def __init__(self, filename, debug=False):
        self.debug = debug
        bytes = list(self.bytes_from_file(filename))
        self.memory = [0b0] * int(0x1000)
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
            print(format(i, '05x').upper(), str(format(bytes[i], '02x')), str(format(bytes[i+1], '02x')), self.parseBytePair(bytes[i], bytes[i+1]))


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
        if oldPC == self.PC: #no jump was made, execute next instruction
            self.PC += 2

        return response

    def executeInstruction(self, firstBytePair, secondBytePair):
        fBL, fBR = self.splitBytePair(firstBytePair)
        sBL, sbR = self.splitBytePair(secondBytePair)
        rightPart = (fBR << 8) + secondBytePair
        if fBL == 0x0:
            if rightPart == 0x000:
                return "NOOP"
            elif fBR == 0x0 and secondBytePair == 0xE0:
                return "CLEAR"
            elif fBR == 0x0 and secondBytePair == 0xEE:
                self.PC = self.stack.pop()
                return "RETURN"
            return "Not implemented yet"
        elif fBL == 0x1:
            self.PC = rightPart
            return "GOTO " + self.f(rightPart)
        elif fBL == 0x2:
            self.stack.append(self.PC)
            self.PC = rightPart
            return "CALL " + self.f(rightPart)
        elif fBL == 0x3:
            if self.V[fBR] == secondBytePair:
                self.PC += SKIP_INSTRUCTION  # skip next instruction
            return "COND.EQ V" + self.f(fBR) + " , 0x" + self.f(secondBytePair)
        elif fBL == 0x4:
            if self.V[fBR] != secondBytePair:
                self.PC += SKIP_INSTRUCTION  # skip next instruction
            return "COND.NEQ V" + self.f(fBR) + " , 0x" + self.f(secondBytePair)
        elif fBL == 0x5:
            if self.V[fBR] == self.V[sBL]:
                self.PC += SKIP_INSTRUCTION  # skip next instruction
            return "COND.VX V" + self.f(fBR) + " , V" + self.f(sBL)
        elif fBL == 0x6:
            self.V[fBR] = secondBytePair
            return "MOV V" + self.f(fBR) + " , 0x" + self.f(secondBytePair)
        elif fBL == 0x7:
            self.V[fBR] += secondBytePair & 0xff # overflow: 255 + 1 = 0
            return "ADD V" + self.f(fBR) + " , 0x" + self.f(secondBytePair)
        elif fBL == 0x8:
            if sbR == 0x0:
                self.V[fBR] = self.V[sBL]
                return "SET V" + self.f(fBR) + " , V" + self.f(sBL)
            elif sbR == 0x1:
                self.V[fBR] = self.V[fBR] | self.V[sBL]
                return "SET.OR V" + self.f(fBR) + " , V" + self.f(sBL)
            elif sbR == 0x2:
                self.V[fBR] = self.V[fBR] & self.V[sBL]
                return "SET.AND V" + self.f(fBR) + " , V" + self.f(sBL)
            elif sbR == 0x3:
                self.V[fBR] = self.V[fBR] ^ self.V[sBL]
                return "SET.XOR V" + self.f(fBR) + " , V" + self.f(sBL)
            elif sbR == 0x4:
                self.V[fBR] += self.V[sBL]
                self.V[0xF] = 1 if self.V[fBR] > 0xff else 0 # V[F] = 1 iff carry
                self.V[fBR] & 0xff # overflow
                return "ADD.V V" + self.f(fBR) + " , V" + self.f(sBL)
            elif sbR == 0x5:
                self.V[fBR] -= self.V[sBL]
                self.V[0xF] = 1 if self.V[fBR] < 0 else 0  # V[F] = 1 iff borrow
                self.V[fBR] & 0xff  # underflow
                return "SUB.V V" + self.f(fBR) + " , V" + self.f(sBL)
            elif sbR == 0x6:
                lsb = self.V[sBL] & 0b1
                self.V[0xF] = lsb
                self.V[fBR] = self.V[sBL] >> 1
                return "SHIFTR.V V" + self.f(fBR) + " , V" + self.f(sBL)
            elif sbR == 0x7:
                self.V[fBR] = self.V[sBL] - self.V[fBR]
                self.V[0xF] = 1 if self.V[fBR] < 0 else 0  # V[F] = 1 iff borrow
                self.V[fBR] & 0xff  # underflow
                return "SUB.V2 V" + self.f(fBR) + " , V" + self.f(sBL)
            elif sbR == 0xE:
                msb = self.V[sBL] & 0x80 #128, most significant bit
                self.V[0xF] = msb
                self.V[sBL] << 1
                self.V[sBL] = self.V[sBL] & 0xff
                self.V[fBR] = self.V[sBL]
                return "SHIFTL.V V" + self.f(fBR) + " , V" + self.f(sBL)
            return "Not implemented yet"
        elif fBL == 0x9:
            if self.V[fBR] != self.V[sBL]:
                self.PC += SKIP_INSTRUCTION  # skip next instruction
            return "COND.NEQV V" + self.f(fBR) + " , V" + self.f(sBL)
        elif fBL == 0xA:
            self.I = rightPart
            return "SET.I 0x" + self.f(rightPart)
        elif fBL == 0xB:
            self.PC = self.V[0] + rightPart
            return "GOTO.V0 " + self.f(rightPart)
        elif fBL == 0xC:
            rNum = randint(0, 255)
            self.V[fBR] = rNum & secondBytePair
            return "RAND.V V" + self.f(fBR) + " , 0x" + self.f(secondBytePair)
        elif fBL == 0xD:
            print("DRAW V" + self.f(fBR) + " , V" + self.f(sBL) + " , 0x" + self.f(sbR))
            bytesToPrint = self.memory[self.I:(self.I + sbR)]
            startX = self.V[fBR]
            startY = self.V[sBL]

            # curPixel = startY*64 + startX
            # numPixelsToPrint = len(bytesToPrint) * 8
            xOffset = 0
            for curByteIndex in range(len(bytesToPrint)):
                curByte = bytesToPrint[curByteIndex]
                curY = startY + curByteIndex
                if curY >= 32:
                    xOffset = (curY / 32) * 8
                    curY = curY % 32

                for i in range(8):
                    curX = startX + i + xOffset
                    whichBitToPrint = 7 - i
                    newPixel = 1 & (curByte >> whichBitToPrint)

                    if curX >= 64 or curY >= 32:
                        continue
                    print(curX, curY)
                    if not self.V[0xF] and self.screen[curY][curX] and newPixel:
                        self.V[0xF] = 1
                    self.screen[curY][curX] = self.screen[curY][curX] ^ newPixel


            # for i in range(numPixelsToPrint):
            #     curY = int(curPixel/64)
            #     curX = curPixel - 64*curY
            #
            #     whichByteToPrint = int(i / 8)
            #     whichBitToPrint = 7 - (i % 8)
            #
            #
            #     print("CHANGED?",curX, curY, self.screen[curY][curX])
            #     curPixel += 1
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
    d = Dissassembler('roms/test.dms', debug=False)
    d.parseBytes(d.memory)
    #output = d.run()
