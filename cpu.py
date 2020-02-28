"""CPU functionality."""

import sys
import re


class CPU:
    """Main CPU class."""

    def __init__(self, prog_name):
        """Construct a new CPU."""
        self.register = [0] * 8
        # These registers only hold values between 0-255.

        self.interrupts_disabled = False
        # R5 is reserved as the interrupt mask (IM)
        # R6 is reserved as the interrupt status (IS)
        # R7 is reserved as the stack pointer (SP)

        self.ram = [0] * 256
        # The LS-8 has 8-bit addressing, so can address 256 bytes of RAM total.

        # Stack Pointer
        self.SP = 0xF4

        # PC: Program Counter, address of the currently executing instruction
        self.PC = 0

        # IR: Instruction Register, contains a copy of the currently executing instruction
        self.IR = [0] * 8

        # MAR: Memory Address Register, holds the memory address we're reading or writing
        self.MAR = [0] * 8

        # MDR: Memory Data Register, holds the value to write or the value just read
        self.MDR = [0] * 8

        # FL: Flags, see below
        self.FL = [0] * 8

        self.opcodes = {
            HLT: self.HLT,
            LDI: self.LDI,
            PRN: self.PRN,
            POP: self.POP,
            PUSH: self.PUSH,
            CALL: self.CALL,
            RET: self.RET
        }

        self.alu_functions = {
            MUL: self.alu,
        }
        self.show = True
        self.load(prog_name)

    def read_flags(self, ):
        pass

    def ram_read(self, MAR):
        return self.ram[MAR]

    # returns the value at the address
    # Memory Address Register (MAR)
    #  Memory Data Register (MDR)

    def ram_write(self, MAR, MDR):
        # writes the value to that memory address.
        self.ram[MAR] = MDR

    def load(self, name):
        """Load a program into memory."""

        address = 0

        with open(name, 'r') as file:
            for line in file:
                try:
                    instruction = int(line[:8], 2)
                    self.ram[address] = instruction
                    self.log(bin(instruction))
                    address += 1
                except ValueError:
                    print(f'Opps on value {line}')

        print(f"loaded {address - 1} lines")
        self.run()

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            # self.fl,
            # self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end = '')

        for i in range(8):
            print(" %02X" % self.reg[i], end = '')

        print()

    def run(self):
        """Run the CPU."""
        count = 0
        while self.PC != 256:

            self.IR = self.ram_read(self.PC)
            self.log("")
            self.log("")
            self.log(
                f"Instruction {count}: {bin(self.IR)[2:6]}  {bin(self.IR)[6:]}")

            operand_a = self.ram_read(self.PC + 1)
            operand_b = self.ram_read(self.PC + 2)

            if self.IR in self.opcodes.keys():
                self.log(self.opcodes[self.IR].__name__)
                self.opcodes[self.IR](operand_a, operand_b)
            else:
                self.alu(self.IR, operand_a, operand_b)

            self.log("Geting set pc flag.")
            setPC = self._and((self.IR >> 4), 0b0001)
            self.log(bin(setPC)[2:])
            if setPC:
                self.log("The instruction set the PC.")
            else:
                numberOfOperands = self.IR >> 6
                self.log(f'# of operands: {numberOfOperands}')
                self.PC += numberOfOperands + 1

            count += 1

    def LDI(self, operand_a, operand_b):
        # LDI register immediate
        # Set the value of a register to an integer.
        if self.show:
            print(f"Moving reg {operand_b} to reg {operand_a}.")
        self.register[operand_a] = operand_b

    def PRN(self, operand_a, operand_b):
        # PRN register pseudo-instruction
        # Print numeric value stored in the given register.
        if self.show:
            print(f"Printing register {operand_a}")

        print(self.register[operand_a])

    def HLT(self, operand_a, operand_b):
        # Halt the CPU (and exit the emulator).
        if self.show:
            print("Halted")
        exit(1)

    def POP(self, a, b):
        if self.show:
            print(f"Popping off the stack at {self.SP}")
            print(f"Moved value to register {a}")
        self.register[a] = self.ram_read(self.SP)
        self.SP -= 1

    def PUSH(self, a, b):
        if self.show:
            print(f"Pushing reg {a} to the stack at {self.SP + 1}")
        self.SP += 1
        self.ram_write(self.SP, self.register[a])

    def CALL(self, a, b):
        newAddres = self.register[a]
        if self.show:
            print(f'Jumping to line {newAddres}')
            print(f"Pushing {self.PC} to the stack at {self.SP + 1}")
            print()
            print()
        self.ram_write(self.SP, self.PC)
        self.SP += 1
        self.PC = newAddres

    def RET(self, a, b):
        # some thing is broken in return
        if self.show:
            print(f"Returning from the call")
            print(f"Geting the address from the atack at {self.SP}")
        self.PC = self.ram_read(self.SP)
        self.SP -= 1

    def alu(self, opp, a, b):

        operations = {
            MUL: self.mul,
            DIV: self.div,
            ADD: self.add,
            SUB: self.sub,
            AND: self._and
        }

        if opp not in operations.keys():
            print(f"Error - The alu doesn't have the operation {bin(opp)[2:]}")
            exit()

        self.register[a] = operations[opp](self.register[a], self.register[b])

    def _and(self, a, b):
        self.log(f"And together {a} and {b}")
        return a & b

    def sub(self, a, b):
        self.log(f"Subtracting {a} and {b}")
        return a - b

    def add(self, a, b):
        self.log(f"Addomg {a} and {b}")
        return a + b

    def div(self, a, b):
        self.log(f"Diving {a} and {b}")
        return a / b

    def mul(self, a, b):
        self.log(f"Multiplying reg {a} and reg {b}")
        return a * b

    def log(self, message):
        if self.show:
            print(message)


HLT = 0b00000001  # halt
LDI = 0b10000010  # LDI register immediate
PRN = 0b01000111  # print

# stack
POP = 0b01000110
PUSH = 0b01000101

CALL = 0b01010000
RET = 0b00010001

# alu
MUL = 0b10100010  # multiply
DIV = 0b10100011
ADD = 0B10100000  # add
SUB = 0b10100001  # subtract

AND = 0b10101000
CMP = 0B10100111
DEC = 0b01100110  # decreement
INC = 0b01100101  # increment
MOD = 0b10100100
NOT = 0b01101001
OR = 0b10101010
XOR = 0b10101011
