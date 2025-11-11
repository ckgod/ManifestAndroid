# Q56) Dagger 2, Hilt

## Dagger 2 및 Hilt란 무엇인가요? {#DH1}
Android에는 다양한 의존성 주입(DI) 라이브러리가 있지만, `Dagger 2`와 `Hilt`는 두드러진 옵션으로 손꼽힙니다. 
두 라이브러리 모두 `Google`에서 개발하고 공식적으로 지원하므로, 대규모 프로젝트에서 신뢰할 수 있는 선택지입니다.

### Dagger 2란 무엇인가요?
[Dagger 2](https://dagger.dev/)는 Android 및 `Jvm` 환경을 위한 완전 정적, 컴파일 타임 의존성 주입(DI) 프레임워크입니다.
객체 생성을 관리하고 의존성을 자동으로 제공하여 모듈성을 향상시키고 애플리케이션 테스트를 용이하게 하도록 설계되었습니다.

`Dagger 2`는 컴파일 타임에 코드를 생성하므로, 리플렉션 기반 `DI` 프레임워크에 비해 더 나은 성능을 보장합니다.
`Dagger 2`는 `@Module`, `@Provides`, `@Inject`와 같은 어노테이션을 사용하여 의존성을 선언하고 요청합니다.

개발자는 `Component`와 `Module`을 통해 의존성 그래프를 생성하며, `Dagger 2`는 이를 런타임에 자동으로 해결합니다.

```kotlin
@Module
class NetworkModule {
    @Provides
    fun provideRetrofit(): Retrofit {
        return Retrofit.Builder()
            .baseUrl("https://example.com")
            .build()
    }
}

@Component(modules = [NetworkModule::class])
interface AppComponent {
    fun inject(activity: MainActivity)
}

class MainActivity : AppCompatActivity() {
    @Inject
    lateinit var retrofit: Retrofit

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        DaggerAppComponent.create().inject(this)
    }
}
```

### Hilt란 무엇인가요? {#H1}
[Hilt](https://dagger.dev/hilt/)는 `Dagger 2` 위에 구축된 Android용 의존성 주입 라이브러리입니다. `Activity`, `Fragment`, `ViewModel`과 같이 Android 라이프사이클을 인식하는 클래스에 스코프가 지정된 사전 정의된 `Component`를 제공하여 `Dagger`를 Android 프로젝트에 통합하는 과정을 단순화합니다.
`Hilt`는 `@HiltAndroidApp` 및 `@AndroidEntryPoint`와 같은 어노테이션을 제공하여 `DI` 설정을 간소화함으로써 `Dagger 2`에서 필요했던 많은 반복적인 코드를 제거합니다. 
또한 `@Singleton` 및 `@ActivityScoped`와 같은 스코프를 정의하여 의존성의 라이프사이클을 관리합니다.

```kotlin
@HiltAndroidApp
class MyApplication : Application()

@AndroidEntryPoint
class MainActivity : AppCompatActivity() {
    @Inject
    lateinit var retrofit: Retrofit

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
    }
}

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    @Provides
    fun provideRetrofit(): Retrofit {
        return Retrofit.Builder()
            .baseUrl("https://example.com")
            .build()
    }
}
```

## Dagger 2와 Hilt의 주요 차이점
1.  **통합 프로세스**: `Dagger 2`는 개발자가 `Component`와 `Injector`를 수동으로 정의해야 하므로 반복적인 코드가 많이 발생할 수 있습니다. `Hilt`는 사전 정의된 `Component`와 라이프사이클을 인식하는 어노테이션을 제공하여 이를 단순화합니다.
2.  **Android 라이프사이클 통합**: `Hilt`는 Android에 특화되어 있으며 `Activity`, `Fragment`, `ViewModel`과 같은 Android `Component`에 대한 내장 지원을 제공합니다. `Dagger 2`는 더 일반적인 목적이며 라이프사이클을 인식하는 `Component`에 대해서는 추가 설정이 필요합니다.
3.  **스코핑**: `Hilt`는 `@Singleton`, `@ActivityScoped`, `@FragmentScoped`와 같이 Android 라이프사이클 클래스와 밀접하게 통합된 사전 정의된 스코프를 제공합니다. `Dagger 2`에서는 스코핑을 위해 수동 설정과 커스텀 어노테이션이 필요합니다.
4.  **코드 단순성**: `Hilt`는 많은 반복적인 코드를 추상화하여 `DI` 설정의 복잡성을 줄이고 초보자에게 더 친숙하게 만듭니다. `Dagger 2`는 유연하고 강력하지만, 개발자가 모든 `Component`와 관계를 수동으로 정의해야 합니다.
5.  **사용 사례**: `Dagger 2`는 복잡하고 커스텀 `DI` 그래프가 필요한 프로젝트에 적합합니다. `Hilt`는 Android 프로젝트를 위해 특별히 설계되었으며, 사용 편의성과 Android `Component`와의 통합에 중점을 둡니다.

## Hilt 및 Dagger 2가 제공하는 어노테이션
`Hilt`는 `Dagger` 위에 구축되면서 Android 특정 기능을 도입하므로, `Hilt`와 `Dagger 2`는 많은 어노테이션을 공유합니다.
아래는 공유, `Hilt` 특정 및 `Dagger` 특정 기능을 강조하는 어노테이션에 대한 통합 요약입니다. 
이러한 구분은 불필요한 중복 없이 명확성을 보장합니다.

### 공유 어노테이션 (Dagger에서 제공하며 Hilt에서 사용)
1.  [`@Inject`](https://docs.oracle.com/javaee/6/api/javax/inject/Inject.html): 의존성 주입을 위한 생성자, 필드 또는 메서드를 표시합니다. 의존성이 어떻게 제공되거나 요청되어야 하는지를 나타내는 데 사용됩니다.
2.  [`@Provides`](https://dagger.dev/api/latest/dagger/Provides.html): `@Module` 내에서 의존성 생성 메서드를 정의합니다. `Hilt`와 `Dagger` 모두 객체를 공급하기 위해 이 어노테이션에 의존합니다.
3.  [`@Module`](https://dagger.dev/api/latest/dagger/Module.html): 클래스를 의존성 제공자의 컨테이너로 선언합니다. `Module`은 관련 의존성 생성 로직을 그룹화합니다.
4.  [`@Binds`](https://dagger.dev/api/latest/dagger/Binds.html): `@Module` 내에서 인터페이스를 구현에 매핑하는 데 사용되며, 의존성을 정의할 때 반복적인 코드를 줄여줍니다.
5.  [`@Qualifier`](https://docs.oracle.com/javaee/7/api/javax/inject/Qualifier.html): 커스텀 어노테이션을 사용하여 동일한 타입의 여러 `binding`을 구분합니다.
6.  [`@Scope`](https://docs.oracle.com/javaee/6/api/javax/inject/Scope.html): 특정 의존성의 라이프사이클을 제어하는 커스텀 스코핑 어노테이션을 정의할 수 있습니다.
7.  [`@Singleton`](https://docs.oracle.com/javaee/7/api/javax/inject/Singleton.html): 의존성이 해당 스코프(일반적으로 앱의 라이프사이클) 내에서 단일 공유 인스턴스를 가져야 함을 지정합니다.
8.  [`@Component`](https://dagger.dev/api/latest/dagger/Component.html): 의존성 그래프의 인터페이스를 정의합니다. `@Component`는 `Module`을 주입 대상에 연결하고 의존성 라이프사이클을 제어합니다.
9.  [`@Subcomponent`](https://dagger.dev/api/latest/dagger/Subcomponent.html): 스코프가 지정된 사용 사례를 위해 `@Component` 내에 더 작은 의존성 그래프를 생성합니다. 종종 자체 라이프사이클을 가진 자식 `Component`를 생성하는 데 사용됩니다.

> {style="note"} `@Inject`, `@Qualifier`, `@Scope`, `@Singleton` 어노테이션은 `Dagger` 자체에서 나온 것이 아니라 Java Specification(`javax.inject` 패키지)에서 유래했습니다.

### Hilt 특정 어노테이션
1.  [`@HiltAndroidApp`](https://dagger.dev/hilt/application): `Application` 클래스에 적용되어 `Hilt`를 부트스트랩하고 전체 앱을 위한 의존성 그래프를 생성합니다.
2.  [`@AndroidEntryPoint`](https://dagger.dev/hilt/android-entry-point): Android `Component`(`Activity`, `Fragment`, `Service` 등)를 주입 대상으로 표시합니다. 커스텀 `Dagger Component`를 정의할 필요를 없앱니다.
3.  [`@InstallIn`](https://dagger.dev/hilt/modules): `@Module`이 설치될 `Component`(`SingletonComponent`, `ActivityComponent` 등)를 지정합니다.
4.  [`@EntryPoint`](https://dagger.dev/hilt/entry-points): `Hilt`가 관리하는 Android `Component` 외부에서 의존성에 접근하기 위한 진입점을 정의하는 데 사용됩니다.
5.  [`@HiltViewModel`](https://dagger.dev/hilt/view-model): `Jetpack ViewModel`을 `Hilt`와 통합하기 위한 특수 어노테이션입니다. 이를 통해 `ViewModel`이 `Hilt`의 의존성 주입을 사용하면서 라이프사이클을 인식할 수 있도록 합니다. `@HiltViewModel` 어노테이션은 생성자를 위해 `@Inject`와 함께 사용되어야 합니다.
6.  [스코프 어노테이션](https://dagger.dev/hilt/components) (`@ActivityRetainedScoped`, `@ViewModelScoped`, `@ActivityScoped`, `@FragmentScoped`, `@ViewScoped`, `@ServiceScoped`): 사용자가 `Component`를 수동으로 정의하고 인스턴스화하는 기존 `Dagger`와 달리, `Hilt`는 자동으로 생성되는 사전 정의된 `Component`를 제공하여 이 프로세스를 단순화합니다. 이러한 `Component`는 다양한 Android 애플리케이션 라이프사이클에 원활하게 통합됩니다. `Hilt`는 또한 내장된 `Component` 및 스코프 어노테이션 세트를 포함하여 의존성 주입을 보다 간소화하고 라이프사이클을 인식하도록 합니다.

`Hilt`는 `@HiltAndroidApp`, `@AndroidEntryPoint`, `@HiltViewModel`과 같은 어노테이션을 도입하여 Android 애플리케이션의 의존성 주입을 단순화합니다. 이러한 추상화는 `Dagger Component`를 수동으로 정의하는 것과 관련된 많은 반복적인 코드를 제거합니다.
포괄적인 개요를 위해 아래 시각적 가이드도 제공하는 [Hilt 및 Dagger 어노테이션 치트 시트](https://developer.android.com/training/dependency-injection/hilt-cheatsheet)를 참조할 수 있습니다.

## 요약
`Dagger 2`와 `Hilt`는 모두 객체 생성 및 관리를 간소화하는 의존성 주입 프레임워크입니다. `Dagger 2`는 더 다재다능하며 모든 Java 또는 Android 프로젝트에서 사용될 수 있지만, 수동 설정이 더 많이 필요합니다. 반면 `Hilt`는 `Dagger 2`를 기반으로 하지만, 라이프사이클을 인식하는 `Component`와 통합하고 반복적인 코드를 줄임으로써 Android용 `DI`를 단순화합니다. 대부분의 Android 프로젝트에는 `Hilt`가 더 편리한 선택이며, `Dagger 2`는 비-Android 프로젝트 또는 고도로 커스텀된 `DI` 요구 사항에 더 적합합니다.

#### Q1
> `Hilt`는 `Dagger 2`에 비해 의존성 주입을 어떻게 단순화하며, Android 애플리케이션에서 `Hilt`를 사용하는 주요 장점은 무엇인가요?

##### A {collapsible="true" #A2}
Hilt는 Dagger의 성능과 기능을 유지하면서, 안드로이드 개발에 필요한 반복적인 설정 코드를 극적으로 자동화하여 의존성 주입을 단순화합니다. 
Dagger 2에서 개발자가 수동으로 처리해야 했던 많은 부분들을 Hilt가 자동으로 처리합니다. 
1. 컴포넌트 생성 및 관리 자동화
   * Dagger 2: 개발자가 `@Component` 인터페이스를 직접 정의하고, `AppComponent`, `ActivityComponent` 등 컴포넌트 간의 상하 관계(Subcomponent 등)를 수동으로 연결해야 했습니다. 
   * Hilt: 이 모든 것을 자동으로 해줍니다. Hilt는 `SingletonComponent`, `ActivityComponent`, `ViewModelComponent` 등 표준화된 컴포넌트 셋을 미리 제공합니다.
2. 안드로이드 프레임워크 클래스 통합
   * Dagger 2: `Activity`, `Fragment`, `ViewModel` 등 안드로이드 클래스에 의존성을 주입하려면 복잡한 설정이 필요했습니다. `Activity`의 `onCreate()` 에서 수동으로 `inject()` 를 호출하고, `ViewModel`을 위해서는 별도로 `ViewModelFactory`를 구현해야 했습니다.
   * Hilt: 
     * `@AndroidEntryPoint`: `Activity`나 `Fragment`에 이 어노테이션 하나만 붙이면, Hilt가 알아서 생명주기에 맞춰 의존성 주입을 실행합니다. 
     * `@HiltViewModel`: `ViewModel`에 이 어노테이션을 붙이면, `ViewModelFactory`를 자동으로 생성하고 관리해줍니다.

#### Q2
> `Dagger`와 `Hilt`에서 `@Provides`와 `@Binds`의 차이점은 무엇이며, 각각 언제 사용해야 하나요?

##### A {collapsible="true" #A3}
`@Provides`와 `@Binds`는 Hilt/Dagger 모듈(`@Module`)내에서 의존성을 제공하는 방법을 정의하는 어노테이션입니다.
둘의 가장 큰 차이점은 객체 생성 로직의 필요 여부와 성능입니다. 

* `@Provides`: 객체를 직접 생성하는 로직이 필요한 경우 (예: `Retrofit.Builder()...build()`)
* `@Binds`: 인터페이스에 구현체를 단순히 연결(바인딩)만 해주는 경우 (성능상 이점)

#### Q3
> `@Singleton`, `@ActivityScoped`, `@ViewModelScoped`를 사용하여 `Hilt`에서 스코핑이 어떻게 작동하는지, 그리고 이러한 스코프가 애플리케이션 내 의존성 라이프타임에 어떤 영향을 미치는지 설명하세요.

##### A {collapsible="true" #A1}
Hilt의 스코핑은 의존성(객체)의 생명주기를 관리하고, 특정 컴포넌트 범위 내에서 인스턴스를 재사용하기 위한 매커니즘 입니다. 
간단히 말해, 스코프는 hilt에게 "이 객첼르 언제까지 살아있게 할 것이며, 이 범위 안에서는 항상 같은 인스턴스를 줘야 해" 라고 알려주는 규칙입니다.

`@Singleton`: 애플리케이션 컴포넌트에 연결되고, 애플리케이션 생명주기와 동일합니다. 즉, 앱이 시작할 때 생성되어 앱이 종료될 때까지 유지됩니다. 
`@ActivityScoped`: 액티비티 컴포넌트에 연결되고, Activity 생명주기와 동일합니다. 
`@ViewModelScoped`: ViewModel의 생명주기와 동일합니다. ViewModel은 구성 변경에도 파괴되지 않습니다. 이 스코프로 주입된 의존성 또한 구성 변경 시에도 파괴되지 않고 그대로 유지됩니다.
 
