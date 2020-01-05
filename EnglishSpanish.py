# -*- coding: utf-8 -*-
# EnglishSpanish.py
# Rev 0
"""Config - for weather.py version 3.4
This is the call:  EnglishSpanish.getWord('<English word here>')
"""

import config


def getWord(EnglishWord):
    '''single call to select from dictionary
    '''
    SpanishDictionary = {
        'and Reboot': 'y Reiniciar',
        'Beans (mm)': 'Frijoles (mm)',
        'Beans (l)': 'Frijoles (l)',
        'Complete': 'Complete',
        'Corn (mm)': 'Maiz (mm)',
        'Corn (l)': 'Maiz (l)',
        'Clock set': 'poner',
        'do it': 'hazlo',
        'exit': 'salir',
        'full': 'todos',
        'Full Irrigation': 'Todos Riego',
        'Irrigation': 'Riego',
        'Irrigation Action': 'Accion de Riego',
        'Loading new s/w': 'Cargano nuevo s/w',
        'Low Battery Shutdown': 'bateria baja-apagado',
        'MX pages': 'Paginas MX',
        'must restart': 'debe reiniciar',
        'next': 'proxima',
        'no errors': 'sin errores',
        'page': 'pagina',
        'partial': 'algunos',
        'Partial Irrigation': 'Algunos Riego',
        'please wait': 'espera por favor',
        'Rain (mm)': 'Lluvias (mm)',
        'Reboot Required!': 'Necesita Reiniciar',
        'Reboot System': 'Sistema Reinicio',
        'replace USB': 'reemplazar USB',
        'set clock': 'Configurar reloj',
        'Set Clock and Exit  ': 'Configurar el Reloj ',
        'sensor count: ': 'recuento:     ',
        'Shutdown System': 'Sistema Apagado',
        'Today': 'Hoy',
        'WAIT': 'ESPERE',
        'while clock sets': 'el reloj',
        'will reboot': 'va a reiniciar',
        'Weather Station': 'Aparato Metelogico',
        'Ystrdy': 'Ayer'
        }

    if(config.language == "English"):
        returnWord = EnglishWord
    else:
        try:
            returnWord = SpanishDictionary[EnglishWord]
        except KeyError:
            returnWord = EnglishWord

    return returnWord
