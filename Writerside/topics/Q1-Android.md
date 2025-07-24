# Q1) Android란?

## Android란 무엇인가요?
Android는 주로 스마트폰 및 태블릿과 같은 모바일 디바이스용으로 설계된 오픈 소스 운영체제이다.
Google에서 개발 및 유지 관리하며 Linux 커널을 기반으로 한다.

### 안드로이드 OS의 주요 기능
1. **오픈 소스 및 커스터마이징 기능**: 안드로이드는 오픈소스([AOSP](https://source.android.com/))로 개발자와 제조업체가 필요에 따라 수정하고 커스터마이징할 수 있다.
2. **SDK를 사용한 애플리케이션 개발**: Android 앱은 주로 Android 소프트웨어 개발 키트(SDK)와 함께 Java 또는 Kotlin을 사용하여 빌드된다. Android Studio 같은 IDE를 사용하여 플랫폼용 애플리케이션을 설계, 개발 및 디버깅 할 수 있다.
3. **풍부한 앱 생태계**: Google Play 스토어는 Android 용 공식 앱 배포 플랫폼으로 게임부터 생산성 도구까지 다양한 카테고리에 걸쳐 수백만 개의 앱을 제공한다. 개발자는 타사 스토어 또는 직접 다운로드를 통해 앱을 톡립적으로 배포할 수도 있다.
4. **멀티태스킹 및 리소스 관리**: Android는 멀티태스킹을 지원하여 사용자가 여러 앱을 동시에 실행할 수 있다. 관리형 메모리 시스템과 가비지 컬렉션을 사용하여 다양한 기기에서 성능을 최적화한다.
5. **다양한 하드웨어 지원**: Android는 저가형 휴대폰부터 플래그십 모델에 이르기까지 다양한 디바이스를 지원하며 다양한 화면 크기, 해상도 및 하드웨어 구성과 폭넓은 호환성을 제공한다.

### 안드로이드 아키텍처
안드로이드 플랫폼 아키텍처는 여러 구성요소로 구성된 모듈식 계층 구조이다.

![android_architecture.png](android_architecture.png)

- **Linux 커널**: Android 운영 체제의 기초를 형성. 하드웨어 추상화를 처리하여 소프트웨어와 하드웨어 간 원활한 상호 작용을 보장. ex) 메모리 및 프로세스 관리, 보안, Wi-Fi, Bluetooth ...
- **하드웨어 추상화 계층(<tooltip term="HAL">HAL</tooltip>)**: Java API 프레임워크를 디바이스 하드웨어에 연결하는 표준 인터페이스를 제공. 라이브러리 모듈로 구성되며, 카메라나 블루투스 같은 특정 하드웨어 구성 요소에 맞게 조정된다. 프레임워크 API가 하드웨어 액세스를 요청하면 Android 시스템은 HAL 모듈을 동적으로 로드하여 처리한다.

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

- **Android 런타임(ART) 및 핵심 라이브러리**: Android 런타임(ART)은 Kotlin 또는 Java에서 컴파일된 바이트코드를 사용하여 애플리케이션을 실행한다. AOT, JIT 컴파일을 지원한다. 핵심 라이브러리는 데이터 구조, File Manipulation, 스레딩을 위한 필수 API를 제공하여 앱 개발을 위한 포괄적인 환경을 제공한다.
- **네이티브 C/C++ 라이브러리**: Android에는 중요한 기능을 지원하기 위해 C 및 C++로 작성된 네이티브 라이브러리 셋이 포함되어 있다. OpenGL과 같은 라이브러리는 그래픽 렌더링, SQLite는 데이터베이스 작업, WebKit은 웹 콘텐츠 표시를 용이하게 한다.
- **안드로이드 프레임워크(API)**: 애플리케이션 프레임워크 계층은 앱 개발을 위한 상위 수준의 서비스와 API를 제공한다. ActivityManager, NotificationManager, Content Provider 등이 포함된다.
- **Application**: 최상위 계층에는 시스템 앱(예: 연락처, 설정) 및 Android SDK를 사용하여 만든 타사 앱과 같은 모든 사용자 대면 앱이 포함된다. 하위 계층에 의존하여 사용자에게 기능을 제공한다.

> Q) Android의 플랫폼 아키텍처는 Linux 커널 , Android 런타임 (ART), 하드웨어 추상화 레이어 (HAL) 등 여러 계층으로 구성
되어 있습니다. 이러한 구성 요소가 애플리케이션 실행과 하드웨어 상호 작용을 보장하기 위해 어떻게 함께 작동하는지 설명
해 주시겠어요 ?