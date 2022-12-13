import logging

logging.basicConfig(filename='log/out.log', filemode='w', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')


def main_hikvisionapi():
    from hikvisionapi import Client

    cam = Client('http://192.168.0.221', 'useruser', '1q2w3e4r')

    response = cam.System.deviceInfo(method='get')
    print(response)

def update_callback(msg):
    """ get updates. """
    print('Callback: {}'.format(msg))


def main_pyHik():
    import pyhik.hikvision
    camera = pyhik.hikvision.HikCamera('http://192.168.0.221', port=80, usr='user', pwd='1q2w3e4r')
    print(camera)
    # Start event stream
    camera.start_stream()
    camera.add_update_callback(update_callback, 1)




if __name__ == '__main__':
    # main_hikvisionapi()
    main_pyHik()