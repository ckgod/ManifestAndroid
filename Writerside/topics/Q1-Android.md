# Q1) Android란?

## Android란 무엇인가요?
Android는 주로 스마트폰 및 태블릿과 같은 모바일 디바이스용으로 설계된 오픈 소스 운영체제이다.
Google에서 개발 및 유지 관리하며 Linux 커널을 기반으로 한다.

### 안드로이드 OS의 주요 기능
1. **오픈 소스 및 커스터마이징 기능**: 안드로이드는 오픈소스([AOSP](https://source.android.com/))로 개발자와 제조업체가 필요에 따라 수정하고 커스터마이징할 수 있다.
2. **SDK를 사용한 애플리케이션 개발**: Android 앱은 주로 **Android 소프트웨어 개발 키트(SDK)** 와 함께 Java 또는 Kotlin을 사용하여 빌드된다. Android Studio 같은 IDE를 사용하여 플랫폼용 애플리케이션을 설계, 개발 및 디버깅 할 수 있다.
3. **풍부한 앱 생태계**: Google Play 스토어는 Android 용 공식 앱 배포 플랫폼으로 게임부터 생산성 도구까지 다양한 카테고리에 걸쳐 수백만 개의 앱을 제공한다. 개발자는 타사 스토어 또는 직접 다운로드를 통해 앱을 독립적으로 배포할 수도 있다.
4. **멀티태스킹 및 리소스 관리**: Android는 멀티태스킹을 지원하여 사용자가 여러 앱을 동시에 실행할 수 있다. 관리형 메모리 시스템과 가비지 컬렉션을 사용하여 다양한 기기에서 성능을 최적화한다.
5. **다양한 하드웨어 지원**: Android는 저가형 휴대폰부터 플래그십 모델에 이르기까지 다양한 디바이스를 지원하며 다양한 화면 크기, 해상도 및 하드웨어 구성과 폭넓은 호환성을 제공한다.

### 안드로이드 아키텍처
안드로이드 플랫폼 아키텍처는 여러 구성요소로 구성된 모듈식 계층 구조이다.

![android_architecture.png](android_architecture.png)

- **Linux 커널**: Android 운영 체제의 기초를 형성. 하드웨어 추상화를 처리하여 소프트웨어와 하드웨어 간 원활한 상호 작용을 보장. ex) 메모리 및 프로세스 관리, 보안, Wi-Fi, Bluetooth ...
  - ART가 스레딩, 저수준 메모리 관리 같은 핵심 기능을 이 Linux 커널에 의존한다.
  - 커널이 담당하는 일은 프로세스/메모리/전력 관리, 그리고 디스플레이,카메라,블루투스,오디오 같은 하드웨어 드라이버이다.
  - Linux 커널을 사용함으로써 안드로이드는 핵심 보안 기능을 활용할 수 있고, 기기 제조사는 잘 알려진 커널을 기반으로 하드웨어 드라이버를 개발할 수 있다.
  - 완전 순수 Linux 커널은 아니고, 안드로이드를 위해 Binder(IPC), Ashmem, Low Memory Killer 같은 것들이 추가된 형태이다.

- **하드웨어 추상화 계층(<tooltip term="HAL">HAL</tooltip>)**: 기기 하드웨어 기능을 상위의 Java API 프레임워크에 노출시키는 표준 인터페이스를 제공. 라이브러리 모듈로 구성되며, 카메라나 블루투스 같은 특정 하드웨어 컴포넌트를 위한 인터페이스를 구현한다. 프레임워크 API가 하드웨어 액세스를 요청하면 Android 시스템은 HAL 모듈을 동적으로 로드하여 처리한다.
  - HAL은 표준 인터페이스를 갖춘 추상화 계층으로, 안드로이드가 저수준 드라이버 구현에 구애받지 않게 해준다.
  - 상위 시스템을 수정하지 않고도 기능을 구현할 수 있게 한다.
  - 삼성, Pixel 같이 제조사마다 카메라 센서가 달라도, 프레임워크 입장에서는 동일한 인터페이스로 카메라에 접근할 수 있는 이유이다.

```kotlin
fun setFlashlight(context: Context, enable: Boolean) {
    try {
        // 1. [Java API 프레임워크]
        // Context를 통해 시스템 서비스인 CameraManager에 접근합니다.
        val cameraManager = context.getSystemService(Context.CAMERA_SERVICE) as CameraManager

        // 2. 사용 가능한 카메라 목록에서 첫 번째 카메라의 ID를 가져옵니다.
        val cameraId = cameraManager.cameraIdList[0]

        // 3. [HAL 호출 트리거]
        // 표준 API인 setTorchMode()를 호출합니다. 이 시점에서 안드로이드 시스템은
        // 해당 기기의 카메라 HAL 모듈을 로드하여 실제 하드웨어를 제어하는
        // 저수준(low-level) 명령을 실행하도록 요청합니다.
        cameraManager.setTorchMode(cameraId, enable)

        /**
         * CameraMamager는 setTorchMode 요청을 받고, "아 카메라 하드웨어 기능이 필요하구나"라고 인지
         * 안드로이드 시스템은 이 기기의 카메라 HAL 모듈(예: carmera.vendor.so)을 로드
         */

        Log.d("HAL_Example", "플래시를 ${if (enable) "켰습니다" else "껐습니다"}.")

    } catch (e: Exception) {
        // 카메라가 없거나 사용할 수 없는 등 다양한 하드웨어 관련 예외를 처리합니다.
        Log.e("HAL_Example", "플래시 제어에 실패했습니다.", e)
    }
}
```
{collapsible="true" collapsed-title="HAL 예제 코드"}

- **Android 런타임(ART)**: Android 런타임(ART)은 Kotlin 또는 Java에서 컴파일된 바이트코드(DEX 파일)를 사용하여 애플리케이션을 실행한다. d8같은 빌드 도구가 Java 소스를 DEX 바이트코드로 컴파일하면 안드로이드 플랫폼에서 실행될 수 있다. 주요 기능에는 AOT(Ahead-of-Time), JIT(Just-in-Time) 컴파일이 포함된다.

- **네이티브 C/C++ 라이브러리**: ART나 HAL같은 많은 안드로이드 핵심 시스템 컴포넌트와 서비스는 C와 C++로 작성된 네이티브 코드로 빌드되며, 네이티브 라이브러리가 필요하다. 안드로이드 플랫폼은 이 네이티브 라이브러리의 기능 일부를 앱에 노출시키는 Java 프레임워크 API를 제공한다.
  - 안드로이드 프레임워크의 Java OpenGL API를 통해 OpenGL ES에 접근할 수 있다.
  - OpenGL과 같은 라이브러리는 그래픽 렌더링, SQLite는 데이터베이스 작업, WebKit은 웹 콘텐츠 표시를 용이하게 한다.

- **안드로이드 프레임워크(API)**: 안드로이드 OS의 전체 기능 세트는 Java언어로 작성된 API를 통해 사용할 수 있다. 애플리케이션 프레임워크 계층은 앱 개발을 위한 상위 수준의 서비스와 API를 제공한다. 
  - ActivityManager: 앱 라이프사이클과 액티비티 스택의 모든 측면을 제어
  - View System: UI 구성
  - Content Provider: 앱이 다른 앱과 데이터를 게시, 공유할 수 있게 함
  - Resource Manager: 문자열, 색상 설정, UI 레이아웃 같은 비,코드 임베디드 리소스에 대한 접근 제공
  - NotificationManager,  Package Manager, Telephony Manager, Location Manager 등

<note>
Jetpack/AndroidX 라이브러리는 엄밀히는 플랫폼 프레임워크의 일부가 아니라 앱과 함께 배포되는 라이브러리이다. 플랫폼 API를 감싸서 더 쓰기 좋게 만든 계층이라고 이해하면 된다.
</note>

- **Application**: 최상위 계층에는 시스템 앱(예: 연락처, 설정) 및 Android SDK를 사용하여 만든 타사 앱과 같은 모든 사용자 대면 앱이 포함된다. 하위 계층에 의존하여 사용자에게 기능을 제공한다.

![aosp_architecture.png](aosp_architecture.png)

```plain text
[앱] Gmarket의 상품 사진 촬영 화면 (Application 계층)
  ↓ Camera2 API 호출
[프레임워크] CameraManager - 권한 체크, 세션 관리 (Android API Framework)
  ↓ Binder IPC
[시스템 서비스] Camera Service - 카메라 접근 중재 (Native + Framework)
  ↓
[HAL] Camera HAL - 제조사가 구현한 카메라 인터페이스
  ↓
[커널] Camera Driver - 실제 센서 제어 (Linux Kernel)
  ↓
[하드웨어] 이미지 센서
```

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Android의 플랫폼 아키텍처는 Linux 커널, Android 런타임(ART), 하드웨어 추상화 레이어(HAL) 등 여러 계층으로 구성되어 있습니다. 이러한 구성 요소가 애플리케이션 실행과 하드웨어 상호 작용을 보장하기 위해 어떻게 함께 작동하는지 설명해 주시겠어요?">

Linux Kernel: 프로세스, 메모리, 전력 관리와 하드웨어 드라이버를 담당합니다. ART가 스레딩과 저수준 메모리 관리를 커널에 의존합니다. 일반 Linux 커널이 아니라 Binder, Ashmem, Low Memory Killer가 추가된 안드로이드 변형입니다.

HAL: 표준 인터페이스를 갖춘 추상화 계층으로, 안드로이드가 저수준 드라이버 구현에 구애받지 않게 해줍니다. 카메라, 블루투스 같은 하드웨어 종류별로 별도의 라이브러리 모듈로 구성되며, 프레임워크 API가 하드웨어 접근을 호출하면 시스템이 해당 모듈을 로드합니다. 제조사가 구현하는 부분이 바로 이 계층입니다.

Native Libraries + ART: libc, OpenGL ES, SQLite, Webkit 같은 C/C++ 라이브러리와, 앱 바이트코드를 실행하는 ART로 구성됩니다. 안드로이드 5.0 이상에서 각 앱은 자신의 프로세스와 자체 ART인스턴스에서 실행되며, d8가 컴파일한 DEX 바이트코드를 AOT와 JIT 방식으로 실행합니다.

Android API Framework: ActivityManager, WindowManager, PackageManager, View System 등 앱이 사용하는 시스템 서비스의 API를 제공합니다.

Application: 시스테 기본 앱과 사용자가 설치한 앱이 동일한 계층에 있으며, 플랫폼 기본 앱이라고 해서 서드파티 앱보다 특별한 지위를 갖지 않습니다.

---

구체적인 예로, 앱에서 상품 등록을 위해 카메라로 사진을 촬영하는 경우를 보겠습니다.

App 계층: 앱이 Camera2 API의 CameraManager.openCamera()를 호출합니다.
Framework 계층: 이 호출은 Binder IPC로 system_server의 Camera Service에 도달합니다. Camera Service는 권한을 확인하고 카메라 접근을 중재합니다.
Native + HAL 계층: Camera Service는 JNI를 통해 네이티브 코드를 호출하고, 네이티브 코드는 제조사가 구현한 Camera HAL 모듈을 로드합니다.
Kernel 계층: HAL은 최종적으로 커널의 카메라 드라이버를 호출하고, 드라이버가 이미지 센서를 제어합니다.

이 흐름에서 주목할 점은, 앱 개발자인 저는 Camera2 API만 알면 되고, 삼성 갤럭시든 픽셀이든 동일한 코드가 동작한다는 것입니다. HAL이 하드웨어 차이를 흡수하고, Binder가 프로세스 격리를 유지하면서 통신을 가능하게 하고, ART가 어느 기기에서든 같은 DEX 바이트코드를 실행해주기 때문입니다. 이것이 각 계층이 함께 작동하여 앱 실행과 하드웨어 상호작용을 보장하는 방식입니다.


</def>
</deflist>