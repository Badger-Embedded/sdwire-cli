sdwire device [-s|--serial] firmware update
yeni fw versiyonlari burada yayinlanacak: https://github.com/Badger-Embedded/sdwire-gen2-fw/releases
bu releaseler github api ile cekilebilir
su an icin cihazda yazili olan fw versiyonu 0.0.0 olarak dusunebiliriz
versiyon karsilastirma islemi python semver ile yapilacak
circuit python usb block devicei bulabilmek icin circup in koduna bakilabilir
circup takili cihazlari tarayip hangisinin circuitpython cihazi olduguna karar veriyor ve
ona gore libraryleri yukluyor
burada dikkat edilmesi gereken nokta su: bir bilgisayara birden fazla sdwire
baglanabilir bu durumda fw update ozellikle belirtilen cihaza yapilmali
eger birden fazla cihaz bagli ise id istenilmeli sonraki asamalarda bu interactive yapilabilir
