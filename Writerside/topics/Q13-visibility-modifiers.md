# Q13) 가시성 수정자의 종류와 범위

Kotlin의 가시성 수정자는 **`public` · `private` · `protected` · `internal`** 네 가지입니다. 아무것도 붙이지 않으면 **`public`** 입니다.

```kotlin
class Example {
    val a = 1                  // public — 기본값
    private val b = 2          // 이 클래스 안에서만
    protected val c = 3        // 이 클래스와 서브클래스에서만
    internal val d = 4         // 같은 모듈 안에서만
}
```

Java를 하다 오면 두 가지가 낯섭니다. **기본값이 `public`이라는 것**, 그리고 **`package-private`이 없다는 것**입니다.

## 네 가지 수정자 {#modifiers}

| 수정자 | 최상위 선언 | 클래스 멤버 |
|---|---|---|
| `public`(기본) | 어디서나 | 어디서나 |
| `private` | **같은 파일 안** | 같은 클래스 안 |
| `protected` | **사용 불가** | 같은 클래스 + 서브클래스 |
| `internal` | 같은 모듈 안 | 같은 모듈 안 |

여기서 `private`의 의미가 위치에 따라 달라진다는 점이 눈에 띕니다. 최상위에 붙이면 "이 **파일** 밖에서는 안 보임"이고, 멤버에 붙이면 "이 **클래스** 밖에서는 안 보임"입니다.

`protected`는 최상위에 쓸 수 없습니다. 상속할 대상이 없기 때문입니다.

```kotlin
protected fun topProtected() = 2
```

```
error: modifier 'protected' is not applicable to 'top level function'.
```

## 모듈의 범위 {#module}

`internal`을 이해하려면 "모듈"의 범위를 알아야 합니다. **함께 컴파일되는 Kotlin 파일의 묶음**입니다.

- Gradle 소스 셋 (안드로이드 프로젝트의 `:app`, `:data` 같은 모듈)
- Maven 프로젝트
- IntelliJ IDEA 모듈
- `kotlinc` 한 번 호출로 컴파일되는 파일들

한 가지 예외가 있습니다. **test 소스 셋은 main 소스 셋의 `internal` 선언에 접근할 수 있습니다.** 그래서 공개 API로 노출하고 싶지 않은 내부 클래스도 테스트는 가능합니다.

## Java와 다른 점 {#vs-java}

면접에서 갈리는 지점입니다.

| | Java | Kotlin |
|---|---|---|
| 기본 가시성 | package-private | **public** |
| package-private | 있음(기본값) | **없음** |
| `protected` 범위 | 서브클래스 **+ 같은 패키지** | 서브클래스**만** |
| 모듈 단위 제한 | 없음 | **`internal`** |

특히 `protected`가 다릅니다. Java에서는 같은 패키지에 있으면 상속하지 않아도 접근할 수 있지만, Kotlin에서는 막힙니다.

```kotlin
package p
open class Parent { protected fun secret() = 1 }
class Other { fun tryIt(p: Parent) = p.secret() }   // 같은 패키지, 상속 안 함
```

```
error: cannot access 'fun secret(): Int': it is protected in 'p.Parent'.
```

Kotlin은 패키지를 가시성 경계로 쓰지 않습니다. 대신 그 자리를 `internal`이 **모듈 단위**로 대체합니다. 패키지는 이름을 나누는 수단일 뿐이라는 입장입니다.

## Pro Tips {#pro-tips}

### 바이트코드로 보는 internal {#internal-bytecode}

JVM이 아는 접근 수준은 `public` · `protected` · `private` · package-private 넷뿐입니다. **"모듈"이라는 개념이 없습니다.**

그래서 Kotlin 컴파일러는 `internal`을 **`public`으로 컴파일하고, 이름을 맹글링해서** 사실상 숨깁니다.

```kotlin
class Holder {
    internal fun memberInternal() = 3
    fun pub() = 5
}
```

`-module-name MyLibrary`로 컴파일한 결과입니다.

```java
public final class Holder {
  public final int memberInternal$MyLibrary();   // 이름이 바뀜
  public final int pub();
}
```

접미사가 모듈 이름입니다. Gradle에서는 보통 `프로젝트명_소스셋` 형태라 `app_main` 같은 이름이 붙습니다.

이 전략은 두 방향으로 동작합니다.

- **다른 Kotlin 모듈** — 컴파일러가 `.class` 메타데이터에서 `internal`임을 읽고 **컴파일 오류**를 냅니다. 맹글링된 이름을 시도하지도 않습니다.
- **Java 등 다른 JVM 언어** — 기술적으로는 `memberInternal$MyLibrary()`로 호출할 수 있지만, 자동 완성에 뜨지 않고 이름 자체가 "내부용"이라는 경고 역할을 합니다.

> **맹글링은 클래스 멤버에만 적용됩니다.** 최상위 `internal` 선언은 이름이 바뀌지 않습니다.
>
> 이유는 맹글링의 목적에 있습니다. 다른 모듈의 하위 클래스가 우연히 같은 이름의 멤버를 선언해 충돌하는 것을 막으려는 장치인데, 최상위 함수는 오버라이드될 수 없어 그런 위험이 없습니다.

같은 코드를 최상위로 옮기면 이렇게 됩니다.

```kotlin
internal fun topLevelInternal() = 1
internal val topLevelInternalVal = 2
```

```java
public final class LibKt {
  public static final int topLevelInternal();            // 그대로
  public static final int getTopLevelInternalVal();      // 그대로
}
```

> 위 결과는 kotlinc 2.2.20으로 컴파일해 `javap`으로 확인한 것입니다. 최상위 `internal` 함수까지 맹글링된다고 설명하는 자료가 있는데, 현재 컴파일러는 그렇게 만들지 않습니다.

### 나머지 수정자의 바이트코드 매핑 {#mapping}

| Kotlin | 바이트코드 |
|---|---|
| `public` | `public` |
| `private`(멤버) | `private` |
| `private`(최상위) | 파일 클래스 안의 `private static` |
| `protected` | `protected` |
| `internal` | `public` + 멤버면 이름 맹글링 |

최상위 `private`도 확인해 보면 파일 클래스(`파일명Kt`) 안의 `private static` 메서드가 됩니다.

```kotlin
private fun topPrivate() = 1
fun caller() = topPrivate()
```

```java
public final class Vis3Kt {
  private static final int topPrivate();
  public static final int caller();
}
```

### 실무 기본값 선택 {#practice}

기본값이 `public`이라는 점이 함정입니다. **아무 생각 없이 쓰면 전부 공개 API가 됩니다.**

- **라이브러리·멀티 모듈 프로젝트** — 밖에 보일 필요가 없으면 `internal`을 기본으로 둡니다. 공개 API 표면이 좁아야 나중에 내부 구현을 바꿀 수 있습니다.
- **단일 모듈 앱** — `internal`과 `public`의 실질 차이가 거의 없습니다. 대신 클래스 안에서는 `private`을 적극적으로 씁니다.
- **`protected`** — 상속을 전제로 설계한 클래스에서만 씁니다. Kotlin 클래스는 기본이 `final`이라 애초에 상속 자체가 옵트인입니다.

> **Compose에서 자주 보는 패턴** — 화면 진입점 Composable만 `public`으로 두고, 내부 조각 Composable은 `private`으로 둡니다. 프리뷰용 Composable도 `private`이 맞습니다. 파일 밖에서 쓸 일이 없기 때문입니다.

## 요약 {#summary}

> **TL;DR** — `public`(기본) · `private` · `protected` · `internal` 네 가지입니다. Java와 달리 기본값이 `public`이고 package-private이 없으며, `protected`가 같은 패키지에는 열리지 않습니다. `internal`은 모듈 단위 제한인데 JVM에 모듈 개념이 없어 `public` + 이름 맹글링으로 구현됩니다. 맹글링은 클래스 멤버에만 적용되고 최상위 선언에는 적용되지 않습니다.

1. **네 가지**: `public`(기본) / `private` / `protected` / `internal`.
2. **`private`의 범위**: 최상위면 같은 **파일**, 멤버면 같은 **클래스**.
3. **`protected`**: 최상위에는 사용 불가. 서브클래스에서만 접근 가능.
4. **Java와의 차이**: 기본값이 `public`, package-private 없음, `protected`가 같은 패키지에 열리지 않음.
5. **모듈**: 함께 컴파일되는 파일 묶음(Gradle 소스 셋 등). test 소스 셋은 main의 `internal`에 접근 가능.
6. **`internal`의 정체**: 바이트코드에는 `public`. 다른 Kotlin 모듈은 컴파일러가 막고, Java에는 맹글링된 이름이 경고 역할.
7. **맹글링 범위**: 클래스 멤버만 `이름$모듈명`으로 바뀜. 최상위 선언은 이름 그대로.
8. **실무**: 기본이 `public`이므로 의식적으로 좁혀야 함. 라이브러리·멀티 모듈이면 `internal`을 출발점으로.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) Kotlin의 가시성 수정자에는 어떤 것들이 있나요?">

`public`, `private`, `protected`, `internal` 네 가지이며 아무것도 붙이지 않으면 `public`입니다. `private`은 최상위 선언에 붙이면 같은 파일 안에서만, 클래스 멤버에 붙이면 그 클래스 안에서만 보입니다. `protected`는 해당 클래스와 서브클래스에서만 접근할 수 있고 최상위 선언에는 사용할 수 없습니다. `internal`은 같은 모듈 안에서만 접근을 허용하는데, 여기서 모듈은 함께 컴파일되는 파일의 묶음, 즉 Gradle 소스 셋이나 Maven 프로젝트 단위를 의미합니다.

</def>
<def title="Q) Kotlin의 가시성이 Java와 다른 점은 무엇인가요?">

세 가지가 다릅니다. 첫째, 기본 가시성이 Java는 package-private이지만 Kotlin은 `public`입니다. 둘째, Kotlin에는 package-private에 해당하는 수정자가 아예 없습니다. Kotlin은 패키지를 가시성 경계로 쓰지 않고 이름을 나누는 수단으로만 취급하며, 그 자리를 모듈 단위인 `internal`이 대신합니다. 셋째, `protected`의 범위가 다릅니다. Java의 `protected`는 서브클래스뿐 아니라 같은 패키지의 코드에도 열려 있지만, Kotlin은 서브클래스에만 허용합니다. 같은 패키지의 다른 클래스에서 접근하면 컴파일 오류가 납니다.

</def>
<def title="Q) internal은 바이트코드에서 어떻게 표현되나요?">

JVM에는 모듈 가시성이라는 개념이 없어서 `public`으로 컴파일되고, 대신 이름이 맹글링됩니다. 클래스 멤버의 경우 `함수명$모듈명` 형태가 되어 `-module-name MyLibrary`로 컴파일하면 `memberInternal$MyLibrary()`가 됩니다. 이 전략은 두 방향으로 작동하는데, 다른 Kotlin 모듈에서는 컴파일러가 클래스 메타데이터에서 `internal`임을 읽고 컴파일 오류를 내고, Java에서는 맹글링된 이름이 자동 완성에 뜨지 않아 사실상 숨겨집니다. 다만 맹글링은 클래스 멤버에만 적용되며 최상위 `internal` 함수나 프로퍼티는 이름이 그대로 유지됩니다. 맹글링의 목적이 다른 모듈의 하위 클래스와 이름이 충돌하는 것을 막는 데 있는데, 최상위 함수는 오버라이드될 수 없어 그런 위험이 없기 때문입니다.

</def>
<def title="Q) protected를 최상위 선언에 쓸 수 없는 이유는?">

`protected`는 "이 클래스와 그 서브클래스에서만 접근 가능"을 의미하는데, 최상위 선언에는 그것을 상속할 클래스라는 개념 자체가 없기 때문입니다. 시도하면 `modifier 'protected' is not applicable to 'top level function'` 오류가 납니다. 최상위 선언에서 접근을 좁히려면 같은 파일로 제한하는 `private`이나 같은 모듈로 제한하는 `internal`을 사용합니다.

</def>
<def title="Q) 모듈 단위로 코드를 숨기고 싶은데 테스트는 어떻게 하나요?">

`internal`로 선언해도 test 소스 셋에서는 접근할 수 있습니다. Gradle에서 test 소스 셋은 main 소스 셋의 `internal` 선언에 접근 가능하도록 예외가 적용되기 때문입니다. 따라서 공개 API로 노출하고 싶지 않은 내부 클래스나 함수도 `internal`로 두고 정상적으로 단위 테스트를 작성할 수 있습니다. 테스트를 위해 굳이 `public`으로 열 필요가 없습니다.

</def>
<def title="Q) Kotlin에서 기본 가시성이 public인 것이 왜 주의할 점인가요?">

아무 수정자도 붙이지 않으면 전부 공개 API가 되기 때문입니다. Java는 기본이 package-private이라 의식하지 않아도 어느 정도 좁혀져 있지만, Kotlin은 반대로 의식적으로 좁혀야 합니다. 라이브러리나 멀티 모듈 프로젝트라면 밖에 보일 필요가 없는 선언을 `internal`로 두는 것이 좋습니다. 공개 API 표면이 좁아야 나중에 내부 구현을 자유롭게 바꿀 수 있기 때문입니다. 단일 모듈 앱이라면 `internal`과 `public`의 실질적 차이는 거의 없으므로 클래스 내부에서 `private`을 적극적으로 쓰는 편이 실효가 큽니다.

</def>
</deflist>
