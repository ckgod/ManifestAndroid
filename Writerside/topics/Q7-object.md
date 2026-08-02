# Q7) object란 무엇이며 일반 클래스와의 차이

`object` 선언은 **클래스 정의와 인스턴스 생성을 한 문장으로 처리**하는 구조입니다. 이름을 선언하는 순간 그 이름이 곧 유일한 인스턴스가 되며, 애플리케이션 전체 생명주기 동안 하나만 존재합니다. Kotlin에서 싱글톤을 만드는 관용적인 방법입니다.

```kotlin
object Logger {
    fun log(message: String) {
        println("Log: $message")
    }
}

fun main() {
    Logger.log("This is a singleton logger.")
    Logger.log("Logging another message.")
}
```

`Logger` 인스턴스를 따로 만들지 않았는데 바로 쓸 수 있습니다. 컴파일러가 인스턴스 생성과 관리를 대신하기 때문입니다.

> **Java에서 싱글톤을 직접 만들어 본 적이 있다면** — private 생성자, static 인스턴스 필드, 스레드 안전을 위한 double-checked locking이나 holder 클래스까지 손으로 써야 했습니다. Kotlin은 그 패턴 전체를 `object` 한 단어로 대체합니다. 뒤에서 볼 바이트코드가 정확히 그 Java 싱글톤 패턴입니다.

## 주요 특성 {#characteristics}

1. **싱글톤** — 애플리케이션 전체 생명주기 동안 인스턴스가 하나만 생성됩니다.
2. **스레드 안전한 초기화** — 멀티스레드 환경에서도 정확히 한 번만 생성되도록 런타임이 보장합니다.
3. **명시적 인스턴스화 불가** — 생성자를 가질 수 없고 `Logger()`처럼 직접 만들 수 없습니다.
4. **지연 초기화** — 처음 접근하는 시점에 생성됩니다. 쓰지 않으면 만들어지지 않습니다.
5. **로컬 선언 불가** — 최상위이거나 다른 클래스·객체 안에 중첩되어야 합니다. 함수 내부에는 선언할 수 없습니다.

## object와 일반 class의 차이 {#vs-class}

| | `object` | `class` |
|---|---|---|
| 인스턴스 수 | 항상 1개 | 필요할 때마다 생성 |
| 생성 방법 | 자동(첫 접근 시) | `MyClass()` 직접 호출 |
| 생성자 | 가질 수 없음 | 가질 수 있음 |
| 목적 | 공유 리소스·유틸리티 | 서로 다른 상태를 가진 객체들 |
| 스레드 안전 초기화 | 언어가 보장 | 직접 구현해야 함 |

`class`는 설계도이고 `object`는 이미 지어진 건물 하나입니다. 상태가 여러 개 필요하면 `class`, 앱 전체가 공유하는 하나가 필요하면 `object`입니다.

## 사용 사례 {#use-cases}

1. **유틸리티 묶음** — 로깅, 포맷팅, 유효성 검사처럼 상태 없이 동작만 모을 때
2. **전역 상수** — 설정 키나 고정값을 한곳에 둘 때
3. **공유 상태 관리** — 캐시나 앱 전역 설정처럼 단일 인스턴스가 필요한 리소스

## Pro Tips {#pro-tips}

### object 선언 vs object 표현식 {#declaration-vs-expression}

같은 `object` 키워드를 쓰지만 완전히 다른 두 기능입니다. 이름이 있으면 선언, 없으면 표현식입니다.

**선언**은 이름 있는 싱글톤을 만듭니다.

```kotlin
object DataProviderManager {
    fun registerDataProvider(provider: DataProvider) { /* ... */ }
}

DataProviderManager.registerDataProvider(myProvider)
```

**표현식**은 그 자리에서 익명 객체를 만듭니다. Android에서 리스너를 붙일 때 쓰던 그 형태입니다.

```kotlin
view.setOnClickListener(object : View.OnClickListener {
    override fun onClick(v: View?) {
        // 이 리스너만을 위해 생성되는 객체
    }
})
```

| | 선언(declaration) | 표현식(expression) |
|---|---|---|
| 이름 | 있음 | 없음(익명) |
| 인스턴스 | 하나만(싱글톤) | 실행할 때마다 새로 생성 |
| 초기화 시점 | 첫 접근 시(지연) | 그 줄에 도달하는 즉시 |
| 선언 위치 | 최상위·중첩만 | 함수 내부 포함 어디든 |
| 외부 스코프 캡처 | 해당 없음 | 가능(클로저) |

특히 **표현식은 싱글톤이 아니라는 점**이 중요합니다. 리스너를 붙이는 코드가 100번 실행되면 객체도 100개 만들어집니다. 이름이 없다고 가벼운 게 아닙니다.

### data object {#data-object}

Kotlin 1.9에서 추가됐습니다. `object`의 단일 인스턴스 보장에 `data class`의 자동 생성 메서드를 얹은 것입니다.

```kotlin
data object Configuration {
    val appName: String = "Dove Letter"
    val version: String = "1.0.0"
}

fun main() {
    println(Configuration)   // Configuration(appName=Dove Letter, version=1.0.0)
}
```

일반 `object`는 `toString()`이 `Configuration@1a2b3c` 같은 형태로 나옵니다. `data object`는 프로퍼티까지 찍어 주므로 로깅·디버깅에서 바로 읽힙니다.

3주차에서 본 `sealed class` 상태 표현과 특히 잘 맞습니다. `Loading`, `Empty`처럼 데이터가 없는 상태를 `data object`로 두면 로그가 깔끔해집니다.

| | `data class` | `object` | `data object` |
|---|---|---|---|
| 인스턴스 | 여러 개 | 하나 | 하나 |
| `toString` 등 자동 생성 | O | X | O |
| 적합한 대상 | 상태가 다른 데이터 모델 | 공유 리소스·유틸 | 단일 불변 데이터·상태 |

### 바이트코드로 보는 object {#bytecode}

`object`가 정말 싱글톤인지는 디컴파일하면 드러납니다.

```kotlin
object LoggerConfig {
    val logLevel: String = "DEBUG"

    fun log(message: String) {
        println("[$logLevel]: $message")
    }

    init {
        println("LoggerConfig initialized.")
    }
}
```

디컴파일하면 교과서적인 Java 싱글톤이 나옵니다.

```java
public final class LoggerConfig {
    private static final String logLevel;

    // 싱글톤 인스턴스를 담는 static final 필드
    public static final LoggerConfig INSTANCE;

    // 외부 인스턴스화를 막는 private 생성자
    private LoggerConfig() {
    }

    // static 초기화 블록에서 인스턴스 생성 + init 로직 실행
    static {
        LoggerConfig var0 = new LoggerConfig();
        INSTANCE = var0;
        logLevel = "DEBUG";
        System.out.println("LoggerConfig initialized.");
    }

    public final void log(String message) {
        System.out.println("[" + logLevel + "]: " + message);
    }
}
```

네 가지가 핵심입니다.

1. **`final` 클래스** — 상속할 수 없습니다.
2. **`INSTANCE` 필드** — Kotlin의 `LoggerConfig.log(...)`는 바이트코드에서 `LoggerConfig.INSTANCE.log(...)`가 됩니다.
3. **`private` 생성자** — `new LoggerConfig()`가 원천 차단됩니다.
4. **`static` 초기화 블록** — `init` 블록과 프로퍼티 초기화가 여기 들어갑니다. JVM이 클래스를 로드할 때 정확히 한 번만 실행되므로, **스레드 안전성은 JVM의 클래스 로딩 보장에서 나옵니다.** 별도의 락이 필요 없는 이유입니다.

`companion object`도 같은 전략으로 컴파일됩니다. 자세한 것은 다음 토픽에서 다룹니다.

## 요약 {#summary}

> **TL;DR** — `object` 선언은 클래스 정의와 단일 인스턴스 생성을 한 번에 처리하는 싱글톤입니다. 생성자를 가질 수 없고, 첫 접근 시 지연 초기화되며, 스레드 안전성은 JVM 클래스 로딩이 보장합니다. 이름이 없는 `object 표현식`은 전혀 다른 물건으로 실행할 때마다 새 인스턴스를 만듭니다. 바이트코드에서는 `INSTANCE` static 필드 + private 생성자 형태의 Java 싱글톤이 됩니다.

1. **싱글톤**: 인스턴스 1개, 생성자 없음, 첫 접근 시 지연 초기화.
2. **class와의 차이**: class는 설계도(여러 인스턴스), object는 이미 만들어진 하나.
3. **선언 vs 표현식**: 선언은 이름 있는 싱글톤, 표현식은 실행마다 새로 생기는 익명 객체.
4. **`data object`**(1.9): 싱글톤 + `toString`·`equals`·`hashCode` 자동 생성. sealed 상태 표현에 유용.
5. **바이트코드**: `final` 클래스 + `public static final INSTANCE` + `private` 생성자 + `static` 초기화 블록.
6. **스레드 안전의 근거**: 락이 아니라 JVM이 클래스를 한 번만 초기화한다는 보장.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) object란 무엇이며 일반 클래스와 어떻게 다른가요?">

`object` 선언은 클래스 정의와 인스턴스 생성을 하나의 문장으로 처리해 싱글톤을 만드는 구조입니다. 일반 클래스는 설계도라서 `MyClass()`로 필요할 때마다 새 인스턴스를 만들고 각자 다른 상태를 가질 수 있지만, `object`는 애플리케이션 전체에서 인스턴스가 하나뿐이고 생성자를 가질 수 없으며 직접 인스턴스화할 수도 없습니다. 첫 접근 시점에 지연 초기화되고, 그 초기화가 스레드 안전하다는 것도 언어가 보장합니다. 공유 리소스·유틸리티·전역 상수에 적합합니다.

</def>
<def title="Q) object 선언과 object 표현식의 차이는?">

이름의 유무가 갈림길입니다. object 선언은 이름이 있는 싱글톤으로, 첫 접근 시 한 번만 초기화되고 앱 전체 생명주기 동안 유지되며 최상위나 중첩 위치에만 둘 수 있습니다. object 표현식은 익명 객체를 만들며, 해당 코드에 도달할 때마다 **새 인스턴스가 생성**되고 그 자리에서 즉시 초기화됩니다. 함수 내부를 포함해 어디서든 쓸 수 있고 둘러싼 스코프의 변수를 캡처할 수 있습니다. `setOnClickListener(object : ...)` 같은 일회성 인터페이스 구현이 대표적인 용도이며, 싱글톤이 아니라는 점을 혼동하기 쉽습니다.

</def>
<def title="Q) object의 스레드 안전한 초기화는 어떻게 보장되나요?">

디컴파일하면 프로퍼티 초기화와 `init` 블록이 Java의 `static { ... }` 초기화 블록 안에 배치되어 있습니다. JVM은 클래스 초기화를 정확히 한 번만, 그리고 스레드 안전하게 수행하도록 명세에 규정되어 있으므로, 별도의 락이나 double-checked locking 없이도 싱글톤 인스턴스가 중복 생성되지 않습니다. 즉 안전성의 근거는 Kotlin 런타임의 동기화 코드가 아니라 JVM의 클래스 로딩 메커니즘입니다.

</def>
<def title="Q) data object는 언제 쓰나요?">

단일 인스턴스이면서 `toString()`·`equals()`·`hashCode()`가 자동 생성되기를 원할 때 사용합니다. 일반 `object`는 `toString()`이 `Configuration@1a2b3c`처럼 출력되어 로그에서 알아보기 어렵지만, `data object`는 프로퍼티를 포함한 형태로 출력됩니다. 전역 설정이나 상수처럼 읽기 전용 단일 인스턴스를 표현할 때, 그리고 `sealed class` 계층에서 `Loading`·`Empty`처럼 데이터가 없는 상태를 표현할 때 특히 유용합니다. Kotlin 1.9에서 도입됐습니다.

</def>
<def title="Q) object는 바이트코드에서 어떤 모습인가요?">

`public final class`로 컴파일되고, 싱글톤 인스턴스를 담는 `public static final INSTANCE` 필드가 생성됩니다. 생성자는 `private`으로 만들어져 외부에서 새 인스턴스를 만들 수 없고, 프로퍼티 초기화와 `init` 블록은 `static` 초기화 블록에 배치됩니다. Kotlin에서 `LoggerConfig.log(...)`라고 쓴 호출은 바이트코드 수준에서 `LoggerConfig.INSTANCE.log(...)`로 변환됩니다. 결국 Java에서 손으로 작성하던 스레드 안전한 싱글톤 패턴을 컴파일러가 대신 만들어 주는 것입니다.

</def>
</deflist>
