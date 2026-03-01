import random
import os

class Mutator:
    """
    Research-grade mutation engine providing bit-flipping, 
    arithmetic mutations, and interest value injection.
    """
    
    INTERESTING_VALUES = [
        0, 1, 2, 0xFFFF, 0xFFFFFFFF, 0x7FFFFFFF,
        -1, -128, 127, 255, 256, 1024, 4096, 65535
    ]

    @staticmethod
    def flip_bit(data: bytearray):
        if not data: return data
        byte_idx = random.randint(0, len(data) - 1)
        bit_idx = random.randint(0, 7)
        data[byte_idx] ^= (1 << bit_idx)
        return data

    @staticmethod
    def flip_byte(data: bytearray):
        if not data: return data
        idx = random.randint(0, len(data) - 1)
        data[idx] ^= 0xFF
        return data

    @staticmethod
    def arithmetic_inc(data: bytearray):
        if not data: return data
        idx = random.randint(0, len(data) - 1)
        data[idx] = (data[idx] + 1) % 256
        return data

    @staticmethod
    def inject_interesting_value(data: bytearray):
        if len(data) < 4: return data
        val = random.choice(Mutator.INTERESTING_VALUES)
        idx = random.randint(0, len(data) - 4)
        # Simplified: inject as 4-byte little endian
        for i in range(4):
            data[idx + i] = (val >> (i * 8)) & 0xFF
        return data

    @staticmethod
    def mutate(data: bytes) -> bytes:
        mutated = bytearray(data)
        strategies = [
            Mutator.flip_bit,
            Mutator.flip_byte,
            Mutator.arithmetic_inc,
            Mutator.inject_interesting_value
        ]
        
        # Apply 1-3 random mutations
        for _ in range(random.randint(1, 3)):
            strategy = random.choice(strategies)
            mutated = strategy(mutated)
            
        return bytes(mutated)
