# Turkey Lottery Sources

## Primary Product List

Milli Piyango Online lists the current public game family and result pages:

- Çılgın Sayısal Loto
- Süper Loto
- Şans Topu
- On Numara
- Hızlı On
- Milli Piyango

Useful public pages:

- `https://www.millipiyangoonline.com/`
- `https://www.millipiyangoonline.com/cekilis-sonuclari`
- `https://www.millipiyangoonline.com/cekilis-takvimi`

## Archive Sources Used

LotoBil provides table-based public archives for:

- Çılgın Sayısal Loto: `https://www.lotobil.com/Sayisal-Loto-Butun-Sonuc-Listesi`
- Süper Loto: `https://www.lotobil.com/Super-Loto-Butun-Sonuc-Listesi`
- Şans Topu: `https://www.lotobil.com/Sans-Topu-Butun-Sonuc-Listesi`
- On Numara: `https://www.lotobil.com/On-Numara-Butun-Sonuc-Listesi`

On Numara rows currently expose year, draw number, and 22 drawn values but not exact draw dates in the table. The fetcher stores these rows in an undated file and marks them as unsuitable for time-series recency/calendar modeling until dated official rows are joined.

## Rule Notes

- Çılgın Sayısal Loto: 6 numbers from 1-90 plus Joker and SüperStar fields.
- Süper Loto: 6 numbers from 1-60.
- Şans Topu: 5 numbers from 1-34 plus 1 number from 1-14.
- On Numara: draws 22 numbers from 1-80; player coupons select 10 numbers.
- Hızlı On: new fast-draw product; player chooses 1 to 10 numbers from 1-80, and the app treats it as a limited-archive adapter until a stable dated API export is available.

## Responsible Use

The data is used for statistical research and portfolio construction. The system must not state or imply guaranteed winnings.
