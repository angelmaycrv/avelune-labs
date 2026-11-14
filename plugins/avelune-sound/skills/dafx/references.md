# Канон: ключевые работы по цифровой обработке звука

Источник для скилла `dafx` и технических скиллов `avelune-sound`. Каждая запись: авторы, название, площадка и год, что делает, что взять. Отметка 🏆 означает премию DAFx. Призёры сверены по сообщениям университетов и организаторов (ноябрь 2026). Если нужна страница или точная формулировка, проверь по архиву dafx.de/paper-archive.

## Призёры DAFx 2018–2026

| Год | Премия | Работа | Что взять |
|-----|--------|--------|-----------|
| 2018, Авейру | 🏆 Лучшая статья | Ólafur Bogason, Kurt James Werner, «Modeling Time-Varying Reactances Using Wave Digital Filters» | Честная модуляция ёмкостей и индуктивностей в WDF: фейзеры, вау, фильтры с переменными элементами |
| 2022, Вена | 🏆 Лучшая статья | Cyrus Vahidi и соавт., «Differentiable Time-Frequency Scattering on GPU» | Дифференцируемые признаки звука для обучения моделей и подбора параметров синтеза |
| 2022, Вена | 🏆 Золотая медаль (по STMS) | Lenny Renault и соавт., «Differentiable Piano Model for MIDI-to-Audio Performance Synthesis» | Физически осмысленный дифференцируемый синтез фортепиано вместо генерации сэмплов |
| 2023, Копенгаген | 🏆 Лучшая статья | Gloria Dal Santo, Karolina Prawda, Sebastian J. Schlecht, Vesa Välimäki, «Differentiable Feedback Delay Network for Colorless Reverberation» | Подбор параметров FDN градиентным спуском, чтобы убрать звон и окраску хвоста |
| 2024, Гилфорд | 🏆 Лучшая статья | Peter Meier, Simon Schwär, Meinard Müller, «A Real-Time Approach for Estimating Pulse Tracking Parameters for Beat-Synchronous Audio Effects» | Эффекты, которые «дышат» в такт живой музыке без синхронизации с DAW |
| 2025, Анкона | 🏆 1-я премия | Thomas Risse, Thomas Hélie, Stefan Bilbao, «Power-Balanced Drift Regulation for Scalar Auxiliary Variable Methods: Application to Real-Time Simulation of Nonlinear String Vibrations» | Устойчивая в реальном времени симуляция нелинейных струн с сохранением энергетического баланса |
| 2025 | 🏆 2-я премия | Eloi Moliner, Michal Švento, Alec Wright, Lauri Juvela, Pavel Rajmic, Vesa Välimäki, «Unsupervised Estimation of Nonlinear Audio Effects: Comparing Diffusion-Based and Adversarial Approaches» | Оценка нелинейного эффекта без пар «вход-выход»: путь к моделированию по готовым записям |
| 2025 | 🏆 2-я премия | Oliviero Massi, Alessandro Ilic Mezza, Riccardo Giampiccolo, Alberto Bernardini, «Training Neural Models of Nonlinear Multi-Port Elements Within Wave Digital Structures Through Discrete-Time Simulation» | Маленькая сеть вместо нелинейного элемента внутри WDF: скорость сети и управляемость схемы |
| 2025 | 🏆 3-я премия | Victor Zheleznov, Stefan Bilbao, Alec Wright, Simon King, «Learning Nonlinear Dynamics in Physical Modelling Synthesis Using Neural Ordinary Differential Equations» | Нейронные ОДУ для нелинейностей в физических моделях инструментов |
| 2025 | 🏆 3-я премия | Vesa Välimäki, Stefan Bilbao, Sebastian J. Schlecht, Roope Salmi, David Zicarelli, «Zero-Phase Sound via Giant FFT» | Удаление фазы всей записи: тембр сохраняется, события перемешиваются во времени, получается реверберационное облако |
| 2026, MIT | 🏆 Лучшая статья | Gloria Dal Santo, Xiaojie Pi, Karolina Prawda, Sebastian J. Schlecht, Vesa Välimäki, «Shimmer Reverberation with Nonlinear Feedback Delay Networks» | Сдвиг высоты и нелинейности в петлях FDN с устойчивым затуханием (правила в `reverb`) |

Призёры DAFx 2016, 2017, 2019–2021 в открытых новостях не нашлись в проверяемом виде; ищи на сайтах конференций соответствующих лет.

## Синтез и генераторы

1. **John Chowning, «The Synthesis of Complex Audio Spectra by Means of Frequency Modulation»**, JAES 1973. FM-синтез. Взять: отношение частот задаёт гармоничность, индекс задаёт яркость; индекс по огибающей громкости для «живых» тембров.
2. **Kevin Karplus, Alex Strong, «Digital Synthesis of Plucked-String and Drum Timbres»**, CMJ 1983. Взять: шум в линии задержки с усреднением, простейшая физическая модель.
3. **David Jaffe, Julius O. Smith, «Extensions of the Karplus-Strong Plucked-String Algorithm»**, CMJ 1983. Взять: точная настройка дробной задержкой, управление затуханием и яркостью, место щипка.
4. **Julius O. Smith, «Physical Modeling Using Digital Waveguides»**, CMJ 1992. Взять: бегущие волны в двух линиях задержки, модели струн, труб, пластин.
5. **Xavier Serra, Julius O. Smith, «Spectral Modeling Synthesis: A Sound Analysis/Synthesis System Based on a Deterministic plus Stochastic Decomposition»**, CMJ 1990. Взять: синусоиды + шум для ресинтеза, морфинга, растяжения.
6. **Robert McAulay, Thomas Quatieri, «Speech Analysis/Synthesis Based on a Sinusoidal Representation»**, IEEE TASSP 1986. Взять: отслеживание синусоидальных треков.
7. **Tim Stilson, Julius O. Smith, «Alias-Free Digital Synthesis of Classic Analog Waveforms»**, ICMC 1996. Взять: BLIT, генераторы классических форм без алиасинга.
8. **Eli Brandt, «Hard Sync Without Aliasing»**, ICMC 2001. Взять: minBLEP для разрывов и жёсткой синхронизации.
9. **Vesa Välimäki, «Discrete-Time Synthesis of the Sawtooth Waveform with Reduced Aliasing»**, IEEE Signal Processing Letters 2005. Взять: DPW, самый дешёвый антиалиасинг пилы.
10. **Vesa Välimäki, Antti Huovilainen, «Antialiasing Oscillators in Subtractive Synthesis»**, IEEE Signal Processing Magazine 2007. Взять: обзор и polyBLEP.
11. **Kees van den Doel, Paul Kry, Dinesh Pai, «FoleyAutomatic: Physically-Based Sound Effects for Interactive Simulation and Animation»**, SIGGRAPH 2001. Взять: модальный синтез ударов и контактов для игр.
12. **Stefan Bilbao, «Numerical Sound Synthesis»**, Wiley 2009. Взять: конечно-разностные схемы для струн, пластин, мембран с гарантией устойчивости.
13. **Curtis Roads, «Microsound»**, MIT Press 2001. Взять: гранулярный синтез и микрозвук.
14. **Andy Farnell, «Designing Sound»**, MIT Press 2010. Взять: процедурные модели звуков мира.

## Реверберация

15. **Manfred Schroeder, «Natural Sounding Artificial Reverberation»**, JAES 1962. Взять: гребенчатые фильтры + фазовращатели, исходная архитектура.
16. **James A. Moorer, «About This Reverberation Business»**, CMJ 1979. Взять: фильтры в петлях, ранние отражения отдельно.
17. **Jean-Marc Jot, Antoine Chaigne, «Digital Delay Networks for Designing Artificial Reverberators»**, AES Convention 1991. Взять: FDN с фильтрами затухания, независимое управление временем по частотам.
18. **Jon Dattorro, «Effect Design, Part 1: Reverberator and Other Filters»**, JAES 1997. Взять: схема пластины с модулированным «баком».
19. **Vesa Välimäki, Julian Parker, Lauri Savioja, Julius O. Smith, Jonathan Abel, «Fifty Years of Artificial Reverberation»**, IEEE TASLP 2012. Взять: карта всех методов, с чего начинать.
20. **Sebastian J. Schlecht, Emanuël Habets, «On Lossless Feedback Delay Networks»**, IEEE Transactions on Signal Processing 2017. Взять: какие матрицы обратной связи действительно сохраняют энергию.
21. **Matti Karjalainen, Hanna Järveläinen, «Reverberation Modeling Using Velvet Noise»**, AES Conference 2007. Взять: разреженный шум ±1 для дешёвой свёртки хвоста.
22. **Jon Fagerström, Benoit Alary, Sebastian J. Schlecht, Vesa Välimäki, «Velvet-Noise Feedback Delay Network»**, DAFx 2020. Взять: бархатные фильтры внутри FDN для плотности при малом числе линий.
23. **Jon Fagerström и соавт., «Non-Exponential Reverberation Modeling Using Dark Velvet Noise»**, JAES 2024. Взять: неэкспоненциальные затухания (гейт, обратная реверберация) дёшево.
24. **Sean Costello (Valhalla DSP), блог и доклад AES 2015 «1000 Years of Reverbs»**. Взять: практика коммерческих ревербераторов, диффузия и металлический звон.

## Задержки, фильтры, эквалайзеры

25. **Timo Laakso, Vesa Välimäki, Matti Karjalainen, Unto Laine, «Splitting the Unit Delay»**, IEEE Signal Processing Magazine 1996. Взять: выбор интерполяции для дробной задержки.
26. **Jon Dattorro, «Effect Design, Part 2: Delay-Line Modulation and Chorus»**, JAES 1997. Взять: хорус, флэнджер, вибрато без артефактов.
27. **Robert Bristow-Johnson, «Audio EQ Cookbook»** (заметка W3C). Взять: формулы биквадов.
28. **Vadim Zavalishin, «The Art of VA Filter Design»**, Native Instruments, ред. 2.1. Взять: TPT, ZDF, устойчивые модулируемые фильтры.
29. **Vesa Välimäki, Joshua Reiss, «All About Audio Equalization: Solutions and Frontiers»**, Applied Sciences 2016. Взять: обзор эквалайзеров, графические и параметрические, линейная фаза.

## Нелинейности и виртуальный аналог

30. **Tim Stilson, Julius O. Smith, «Analyzing the Moog VCF with Considerations for Digital Implementation»**, ICMC 1996. Взять: почему наивная дискретизация лестницы сдвигает резонанс.
31. **Antti Huovilainen, «Non-Linear Digital Implementation of the Moog Ladder Filter»**, DAFx 2004. Взять: tanh в каждом каскаде, компенсация задержки.
32. **David Yeh, Jonathan Abel, Julius O. Smith, «Simulation of the Diode Limiter in Guitar Distortion Circuits by Numerical Solution of Ordinary Differential Equations»**, DAFx 2007. Взять: численное решение ОДУ диодного ограничителя, сравнение методов.
33. **Martin Holters, Udo Zölzer, «Physical Modelling of a Wah-Wah Effect Pedal as a Case Study for Application of the Nodal DK Method to Circuits with Variable Parts»**, DAFx 2011. Взять: метод DK с потенциометрами.
34. **Alfred Fettweis, «Wave Digital Filters: Theory and Practice»**, Proceedings of the IEEE 1986. Взять: основы WDF.
35. **Kurt James Werner, Julius O. Smith, Jonathan Abel, «Wave Digital Filter Adaptors for Arbitrary Topologies and Multiport Linear Elements»**, DAFx 2015. Взять: R-адаптеры для схем, которые не раскладываются в дерево.
36. **Julian Parker, Vadim Zavalishin, Efflam Le Bivic, «Reducing the Aliasing of Nonlinear Waveshaping Using Continuous-Time Convolution»**, DAFx 2016. Взять: ADAA первого порядка.
37. **Fabián Esqueda, Vesa Välimäki, Stefan Bilbao, «Rounding Corners with BLAMP»**, DAFx 2016. Взять: поправки в точках излома при жёстком ограничении.
38. **Stefan Bilbao, Fabián Esqueda, Julian Parker, Vesa Välimäki, «Antiderivative Antialiasing for Memoryless Nonlinearities»**, IEEE Signal Processing Letters 2017. Взять: ADAA второго порядка.
39. **Martin Holters, «Antiderivative Antialiasing for Stateful Systems»**, DAFx 2019. Взять: ADAA для систем с памятью.
40. **Jatin Chowdhury, «Real-Time Physical Modelling for Analog Tape Machines»**, DAFx 2019. Взять: гистерезис ленты в реальном времени (открытый плагин CHOW Tape).
41. **Martin Vicanek, «Note on Alias Suppression in Digital Distortion»**. Взять: ADAA + 4× передискретизации против жёсткой сатурации, дешёвый шейпер x/√(1+x²).

## Динамика

42. **Dimitrios Giannoulis, Michael Massberg, Joshua Reiss, «Digital Dynamic Range Compressor Design — A Tutorial and Analysis»**, JAES 2012. Взять: формулы колена, правильный детектор, прямая и обратная связь.
43. **ITU-R BS.1770-5** (2023) и **EBU R 128** (2020). Взять: измерение громкости, гейтинг, true peak.

## Время, высота, спектр

44. **James Flanagan, Roger Golden, «Phase Vocoder»**, Bell System Technical Journal 1966. Взять: исходная идея.
45. **Mark Dolson, «The Phase Vocoder: A Tutorial»**, CMJ 1986. Взять: понятное введение.
46. **Werner Verhelst, Marc Roelands, «An Overlap-Add Technique Based on Waveform Similarity (WSOLA) for High Quality Time-Scale Modification of Speech»**, ICASSP 1993. Взять: растяжение речи и ударных.
47. **Jean Laroche, Mark Dolson, «Improved Phase Vocoder Time-Scale Modification of Audio»**, IEEE TSAP 1999. Взять: блокировка фазы вокруг пиков.
48. **Axel Röbel, «A New Approach to Transient Processing in the Phase Vocoder»**, DAFx 2003. Взять: сохранение атак при растяжении.
49. **Axel Röbel, Xavier Rodet, «Efficient Spectral Envelope Estimation and Its Application to Pitch Shifting and Envelope Preservation»**, DAFx 2005. Взять: сдвиг высоты голоса без эффекта бурундука.
50. **Derry FitzGerald, «Harmonic/Percussive Separation Using Median Filtering»**, DAFx 2010. Взять: простое разделение гармоник и ударных медианными фильтрами.
51. **Jonathan Driedger, Meinard Müller, Sebastian Ewert, «Improving Time-Scale Modification of Music Signals Using Harmonic-Percussive Separation»**, IEEE Signal Processing Letters 2014. Взять: гибрид вокодера и OLA.
52. **Jonathan Driedger, Meinard Müller, «A Review of Time-Scale Modification of Music Signals»**, Applied Sciences 2016. Взять: обзор и сравнение методов, открытый набор инструментов.
53. **Zdeněk Průša, Nicki Holighaus, «Phase Vocoder Done Right»**, EUSIPCO 2017. Взять: восстановление фазы по градиенту (PGHI).
54. **Steven Boll, «Suppression of Acoustic Noise in Speech Using Spectral Subtraction»**, IEEE TASSP 1979. Взять: основа шумоподавления.

## Пространство

55. **Ville Pulkki, «Virtual Sound Source Positioning Using Vector Base Amplitude Panning»**, JAES 1997. Взять: VBAP.
56. **Christian Nachbar, Franz Zotter, Etienne Deleflie, Alois Sontacchi, «AmbiX: A Suggested Ambisonics Format»**, Ambisonics Symposium 2011. Взять: ACN и SN3D как стандарт обмена.
57. **Benoit Alary, Archontis Politis, Vesa Välimäki, «Velvet-Noise Decorrelator»**, DAFx 2017. Взять: дешёвая декорреляция для ширины и диффузного поля.
58. **Jens Blauert, «Spatial Hearing»**, MIT Press 1997. Взять: как слух определяет направление.

## Нейросети и дифференцируемая обработка

59. **Eero-Pekka Damskägg, Lauri Juvela, Etienne Thuillier, Vesa Välimäki, «Deep Learning for Tube Amplifier Emulation»**, ICASSP 2019. Взять: WaveNet-подобная модель усилителя.
60. **Alec Wright, Eero-Pekka Damskägg, Vesa Välimäki, «Real-Time Black-Box Modelling with Recurrent Neural Networks»**, DAFx 2019. Взять: LSTM и GRU для педалей и усилителей в реальном времени.
61. **Alec Wright, Vesa Välimäki, «Perceptual Loss Function for Neural Modelling of Audio Systems»**, ICASSP 2020. Взять: ESR с предыскажением.
62. **Jesse Engel, Lamtharn Hantrakul, Chenjie Gu, Adam Roberts, «DDSP: Differentiable Digital Signal Processing»**, ICLR 2020. Взять: сеть управляет синтезатором.
63. **Boris Kuznetsov, Julian Parker, Fabián Esqueda, «Differentiable IIR Filters for Machine Learning Applications»**, DAFx 2020. Взять: обучение рекурсивных фильтров.
64. **Fabián Esqueda, Boris Kuznetsov, Julian Parker, «Differentiable White-Box Virtual Analog Modeling»**, DAFx 2021. Взять: подбор параметров схемы по записям.
65. **Antoine Caillon, Philippe Esling, «RAVE: A Variational Autoencoder for Fast and High-Quality Neural Audio Synthesis»**, arXiv 2021. Взять: перенос тембра в реальном времени.
66. **Christian Steinmetz, Joshua Reiss, «Efficient Neural Networks for Real-Time Modeling of Analog Dynamic Range Compression»**, AES Convention 2022. Взять: TCN для компрессоров.
67. **Ben Hayes, Jordie Shier, György Fazekas, Andrew McPherson, Charalampos Saitis, «A Review of Differentiable Digital Signal Processing for Music and Speech Synthesis»**, Frontiers in Signal Processing 2024. Взять: обзор всего направления.
68. **Jean-Marc Valin, «A Hybrid DSP/Deep Learning Approach to Real-Time Full-Band Speech Enhancement»** (RNNoise), MMSP 2018. Взять: маленькая сеть + DSP для шумоподавления.

## Книги-основы

- Udo Zölzer (ред.), «DAFX: Digital Audio Effects», 2-е изд., Wiley 2011.
- Joshua Reiss, Andrew McPherson, «Audio Effects: Theory, Implementation and Application», CRC Press 2014.
- Will Pirkle, «Designing Audio Effect Plugins in C++», 2-е изд., Routledge 2019.
- Julius O. Smith, онлайн-книги CCRMA: «Mathematics of the DFT», «Introduction to Digital Filters», «Physical Audio Signal Processing», «Spectral Audio Signal Processing».
- Vadim Zavalishin, «The Art of VA Filter Design».
- Bob Katz, «Mastering Audio», 3-е изд., 2015; Mike Senior, «Mixing Secrets for the Small Studio», 2-е изд., 2018.
- Michel Chion, «Audio-Vision», 1990; Walter Murch, «In the Blink of an Eye», 1995.
