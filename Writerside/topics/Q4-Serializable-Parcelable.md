# Q4) Serializable, Parcelable

## Serializable과 Parcelable의 차이는 무엇인가요?
안드로이드에서 Serializable과 Parcelable은 모두 서로 다른 컴포넌트(예: Activity, Fragment)간에 데이터를 전달하는 데 사용되는 매커니즘이지만
성능과 구현 측면에서 서로 다르게 작동한다.

### Serializable
- Java 표준 인터페이스: Serializable은 객체를 바이트 스트림으로 변환하여 Activity 간에 전달하거나 Disk에 기록할 수 있도록 하는 데 사용되는 표준 Java 인터페이스이다.
- 리플렉션 기반: Java 리플렉션을 통해 작동하며, 이는 시스템이 런타임에 클래스와 해당 필드를 동적으로 검사하여 객체를 직렬화한다는 의미이다.
- 성능: Serializable은 리플렉션이 느리기 때문에 Parcelable에 비해 속도가 느리다. 또한 직렬화하는 동안 많은 임시 객체를 생성하여 메모리 오버헤드가 증가한다.
- 사용 사례: Serializable은 성능이 중요하지 않은 시나리오나 안드로이드 전용이 아닌 코드베이스를 다룰 때 유용하다.

### Parcelable
- 안드로이드 전용 인터페이스: Parcelable은 Android 컴포넌트 내의 고성능 프로세스 간 통신(<tooltip term="IPC">IPC</tooltip>)을 위해 특별히 설계된 Android 전용 인터페이스이다.
- 성능: Parcelable은 Android에 최적화되어 있고 리플렉션에 의존하지 않기 때문에 Serializable보다 빠르다. 또한 임시 객체를 많이 생성하지 않아 가비지 컬렉션을 최소화한다.
- 사용 사례: 성능이 중요한 경우, 특히 IPC나 Activity 또는 Service 간에 데이터를 전달할 때 Parcelable을 선호한다.

최신 안드로이드 개발에서, [kotlin-parcelize Plugin](https://plugins.gradle.org/plugin/org.jetbrains.kotlin.plugin.parcelize)은 구현을 자동으로 생성하여 `Parcelable` 객체를 생성하는 프로세스를 간소화 한다.
이 접근 방식은 이전의 수동 매커니즘에 비해 더 효율적이다. 클래스에 `@Parcelize`로 주석을 달기만 하면 플러그인이 필요한 Parcelable 구현을 생성한다.

```Kotlin
@Parcelize
class User(val firstName: String, val lastName: String, val age: Int) : Parcelable
```

위 어노테이션을 달면 writeToParcel과 같은 메서드를 재정의하거나 구현할 필요가 없다.

### 주요 차이점

| 기능                                | **Serializable** | **Parcelable**      |
|-----------------------------------|------------------|---------------------|
| **유형**                            | 표준 Java 인터페이스    | 안드로이드 전용 인터페이스      |
| **성능**                            | 느림, 리플렉션 사용      | 더 빠름, 안드로이드 최적화 대상  |
| **객체 생성<br>(임시 객체 - 가비지 컬렉션 대상)** | 더 많은 객체 생성       | 객체를 덜 생성            |
| **사용 사례**                         | 일반적인 Java 사용에 적합 | Android, 특히 IPC에 선호 |

### 요약
일반적으로 Android 앱의 경우 대부분 사용 사례에서 성능이 더 우수하므로 Parcelable을 사용하는 게 좋다.
- 간단한 경우나 성능이 중요하지 않은 작업을 처리할 때, 또는 Android 전용이 아닌 코드로 작업할 때는 `Serializable`을 사용
- 안드로이드의 IPC 매커니즘에 훨씬 더 효율적이므로 퍼포먼스가 중요한 안드로이드 전용 컴포넌트로 작업할 때는 `Parcelable`을 사용

> Q) 안드로이드에서 Serializable과 Parcelable의 주요 차이점은 무엇이며 , 일반적으로 컴포넌트 간 데이터 전달에 Parcelable
이 선호되는 이유는 무엇인가요 ?

