# Q6) Application Class

## Application Class란 무엇인가요?
안드로이드의 Application Class 는 앱의 **전역(global) 상태**와 생명주기를 관리하기 위한 기본 클래스이다.
이 클래스는 앱의 진입점(entry point) 역할을 하며, 액티비티, 서비스, 브로드캐스트 리시버 등 다른 어떤 컴포넌트보다도 먼저 초기화된다.
Application 클래스는 앱의 생명주기 전체에서 접근할 수 있는 컨텍스트를 제공하므로, **공유 리소스**를 초기화하는 데 이상적이다.

### Application Class의 목적 {#purpose-application-class}
Application Class는 전역 상태를 유지하고 애플리케이션 전체 초기화를 수행하도록 설계되어있다. 
개발자는 종종 이 클래스를 재정의하여 의존성을 설정하고, 라이브러리를 구성하고, Activity 및 Service 전반에서 지속되어야 하는 리소스를 관리한다.

기본적으로 모든 Android 애플리케이션은 AndroidManifest.xml 파일에 커스텀 클래스가 지정되지 않는 한 Application 클래스 기본 구현을 사용한다.

### Application Class의 주요 메서드 {#method-application-class}
1. **`onCreate()`**: `onCreate`메서드는 앱 프로세스가 생성될 때 호출된다. 일반적으로 데이터베이스 인스턴스, 네트워크 라이브러리 또는 Analytics 도구와 같은 애플리케이션 전체 종속성을 초기화하는 곳이다. 이 메서드는 애플리케이션 생명주기 동안 한 번만 호출된다. 
2. **`onTerminate()`**: 이 메서드는 에뮬레이트된 환경에서 애플리케이션이 종료될 때 호출된다. 안드로이드가 호출을 보장하지 않기 때문에 실제 프로덕션 디바이스에서는 호출되지 않는다.
3. **`onLowMemory()`, `onTrimMemory()`**: 이 메서드는 시스템에서 메모리 부족 상태를 감지하면 트리거된다. `onLowMemory()`는 이전 API 레벨에서 사용되며, `onTrimMemory()`는 앱의 현재 메모리 상태를 기반으로 보다 세분화된 제어 기능을 제공한다.

### Application Class 사용 방법 {#how-to-use-custom-application-class}
Custom Application Class를 정의하려면 Application Class를 확장하고 AndroidManifest.xml 파일에 `<Application>` 태그 아래 지정 해야한다.

```Kotlin
class CustomApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        // initialize global dependencies
    }
}
```

```xml
<application
    android:name=".CustomApplication"
    ... >
    ...
</application>
```

### Application Class 사용 사례 {#usage-application-class}
1. **글로벌 리소스 관리**: 데이터베이스, SharedPreferences 또는 네트워크 클라이언트와 같은 리소스는 한 번 설정해 두었다가 재사용할 수 있다.
2. **컴포넌트 초기화**: 앱의 생명 주기 동안 원활한 기능을 보장하려면 애플리케이션의 시작 프로세스 중에 Firebase Analytics, Timber 및 유사한 도구를 적절하게 초기화해야 한다.
3. **의존성 주입**: Dagger나 Hilt와 같은 프레임워크를 초기화하여 앱 전체에 의존성을 제공할 수 있다.

### **권장 사항 (Best Practices)**
1.  앱 실행이 지연되는 것을 막기 위해, **`onCreate()`** 메서드 내에서 시간이 오래 걸리는 작업을 수행하는 것을 피해야 한다.
2.  **`Application` 클래스**를 관련 없는 로직을 모아두는 용도로 사용하지 말아라. 전역(global) 상태 초기화 및 리소스 관리와 같은 핵심적인 역할에만 집중해야 한다.
3.  `Application` 클래스에서 공유 리소스를 관리할 때는 **스레드 안전성(thread safety)을 반드시 보장**해야 한다.

### 요약
`Application` 클래스는 앱 전반에 걸쳐 사용되어야 하는 리소스를 초기화하고 관리하는 중추적인 역할을 한다.
이 클래스는 전역(global) 설정을 위한 중요하고 기본적인 API지만, 코드의 명확성을 유지하고 불필요한 복잡성을 피하려면 진정으로 전역적인 성격의 작업에만 제한적으로 사용해야 한다.

> Q) `Application` 클래스의 목적은 무엇이고, 라이프사이클 및 리소스 관리 측면에서 Activity와 어떻게 다른가요?