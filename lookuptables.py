import pandas as pd
''

drivers = [['44', 'HAM', 'Mercedes'], ['77', 'BOT', 'Mercedes'],
           ['5', 'VET', 'Ferrari'], ['16', 'LEC', 'Ferrari'],
           ['33', 'VER', 'Red Bull'], ['23', 'ALB', 'Red Bull'],
           ['55', 'SAI', 'McLaren'], ['4', 'NOR', 'McLaren'],
           ['11', 'PER', 'Racing Point'], ['18', 'STR', 'Racing Point'],
           ['3', 'RIC', 'Renault'], ['31', 'OCO', 'Renault'],
           ['26', 'KVY', 'Alpha Tauri'], ['10', 'GAS', 'Alpha Tauri'],
           ['8', 'GRO', 'Haas F1 Team'], ['20', 'MAG', 'Haas F1 Team'],
           ['7', 'RAI', 'Alfa Romeo'], ['99', 'GIO', 'Alfa Romeo'],
           ['6', 'LAT', 'Williams'], ['63', 'RUS', 'Williams'],
           ['88', 'KUB', 'Alfa Romeo']]

drivers_pd = pd.DataFrame(drivers, columns=('Number', 'Abb', 'Team'))


def driver_query(by='', value='', get=''):
    result = drivers_pd.query('{} =="{}"'.format(by, value))[get]
    if len(result) == 1:
        return result.values[0]
    else:
        return result


def get_driver_abbs():
    data = list()
    for drv in drivers:
        data.append(drv[1])
    return data


channel_names = {'0': 'RPM', '2': 'Speed', '3': 'nGear', '4': 'Throttle', '5': 'Brake', '45': 'DRS'}
json_channel_names = list()
[json_channel_names.append({'id': _id, 'name': channel_names[_id]}) for _id in channel_names.keys()]
