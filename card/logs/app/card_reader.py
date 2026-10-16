"""
Модуль для работы с устройствами считывания смарт-карт (PC/SC)
Поддержка ридеров Advancer Card Systems ACR1281U и совместимых
"""
from smartcard.System import readers
from smartcard.Exceptions import NoCardException, CardConnectionException
from smartcard.util import toHexString


def get_available_readers():
    """Получить список доступных устройств считывания"""
    try:
        available = readers()
        return [str(r) for r in available]
    except Exception as e:
        return []


def read_card_number(reader_name=None):
    """
    Считать номер карты с устройства
    
    Args:
        reader_name: имя устройства (если None, используется первое доступное)
    
    Returns:
        dict: {'success': bool, 'card_number': str|None, 'error': str|None}
    """
    try:
        # Получаем список устройств
        available_readers = readers()
        
        if not available_readers:
            return {
                'success': False,
                'card_number': None,
                'error': 'Устройства считывания не найдены'
            }
        
        # Выбираем устройство
        if reader_name:
            reader = None
            for r in available_readers:
                if str(r) == reader_name:
                    reader = r
                    break
            if not reader:
                return {
                    'success': False,
                    'card_number': None,
                    'error': f'Устройство {reader_name} не найдено'
                }
        else:
            # Используем первое доступное устройство
            reader = available_readers[0]
        
        # Подключаемся к устройству
        connection = reader.createConnection()
        connection.connect()
        
        try:
            # Команда для получения UID карты (APDU команда)
            # Для ISO 14443 Type A карт
            get_uid_apdu = [0xFF, 0xCA, 0x00, 0x00, 0x00]
            
            data, sw1, sw2 = connection.transmit(get_uid_apdu)
            
            if sw1 == 0x90 and sw2 == 0x00:
                # Успешно получили UID
                card_number = toHexString(data).replace(' ', '')
                return {
                    'success': True,
                    'card_number': card_number,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'card_number': None,
                    'error': f'Ошибка чтения карты: SW1={sw1}, SW2={sw2}'
                }
        except NoCardException:
            return {
                'success': False,
                'card_number': None,
                'error': 'Карта не обнаружена в устройстве'
            }
        except CardConnectionException as e:
            return {
                'success': False,
                'card_number': None,
                'error': f'Ошибка подключения к карте: {str(e)}'
            }
        finally:
            connection.disconnect()
            
    except Exception as e:
        return {
            'success': False,
            'card_number': None,
            'error': f'Ошибка устройства: {str(e)}'
        }


def test_reader_connection():
    """Протестировать подключение к устройству считывания"""
    readers_list = get_available_readers()
    
    if not readers_list:
        return {
            'success': False,
            'message': 'Устройства считывания не найдены. Проверьте подключение.',
            'readers': []
        }
    
    # Пробуем прочитать карту с первого устройства
    result = read_card_number(readers_list[0])
    
    if result['success']:
        return {
            'success': True,
            'message': f'Устройство найдено: {readers_list[0]}',
            'readers': readers_list,
            'card_number': result['card_number']
        }
    else:
        return {
            'success': True,
            'message': f'Устройство найдено: {readers_list[0]}, но карта не прочитана: {result["error"]}',
            'readers': readers_list,
            'card_number': None
        }
