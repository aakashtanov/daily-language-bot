NUMBERS = {
    'DE': {
        1: 'eins', 2: 'zwei', 3: 'drei', 4: 'vier', 5: 'fünf',
        6: 'sechs', 7: 'sieben', 8: 'acht', 9: 'neun', 10: 'zehn',
        11: 'elf', 12: 'zwölf', 13: 'dreizehn', 14: 'vierzehn',
        15: 'fünfzehn', 16: 'sechzehn', 17: 'siebzehn', 18: 'achtzehn',
        19: 'neunzehn'
    },
    'EN': {
        1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five',
        6: 'six', 7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten',
        11: 'eleven', 12: 'twelve', 13: 'thirteen', 14: 'fourteen',
        15: 'fifteen', 16: 'sixteen', 17: 'seventeen', 18: 'eighteen',
        19: 'nineteen'
    }
}


TENS = {
    'DE': {
        20: 'zwanzig', 30: 'dreißig', 40: 'vierzig', 50: 'fünfzig',
        60: 'sechzig', 70: 'siebzig', 80: 'achtzig', 90: 'neunzig'
    },
    'EN': {
        20: 'twenty', 30: 'thirty', 40: 'forty', 50: 'fifty',
        60: 'sixty', 70: 'seventy', 80: 'eighty', 90: 'ninety'
    }
}


for i in range(20, 100):
    tens = (i // 10) * 10
    ones = i % 10
    if ones == 0:
        NUMBERS['DE'][i] = TENS['DE'][i]
        NUMBERS['EN'][i] = TENS['EN'][i]
    else:
        NUMBERS['DE'][i] = NUMBERS['DE'][ones] + 'und' + TENS['DE'][tens]
        NUMBERS['EN'][i] = TENS['EN'][tens] + NUMBERS['EN'][ones]
