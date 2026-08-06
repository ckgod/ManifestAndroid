# Q10) backing field와 backing property의 차이점은 무엇인가

Kotlin의 프로퍼티는 **필드가 아니라 접근자(getter/setter)** 입니다. 값을 실제로 저장할 공간이 필요하면 그때 저장소가 따로 붙는데, 그 저장소를 만드는 방식이 두 가지입니다.

- **backing field** — 컴파일러가 **암시적으로** 만들어 주는 저장소. `field` 키워드로만 접근합니다.
- **backing property** — 개발자가 **명시적으로** 선언하는 별도 프로퍼티. 보통 `_name`처럼 밑줄을 붙입니다.

이름이 비슷하지만 만들어지는 주체와 제어 범위가 다릅니다.

## backing field {#backing-field}

커스텀 getter나 setter 안에서 값을 읽거나 쓰려면 저장 공간이 필요합니다. 그런데 프로퍼티 이름을 그대로 쓰면 자기 자신을 다시 호출하게 됩니다. 이 문제를 풀기 위해 Kotlin은 `field`라는 예약어를 제공합니다.

```kotlin
var name: String = "Default"
    get() = field.uppercase()       // 저장된 값을 읽어 가공해서 반환
    set(value) {
        field = value.trim()        // 가공해서 저장
    }
```

`field`는 **접근자 안에서만** 쓸 수 있습니다. 클래스 다른 곳에서 `field`를 참조하면 컴파일 오류입니다.

```kotlin
class User {
    var age: Int = 0
        set(value) {
            field = if (value < 0) 0 else value   // 음수를 0으로 보정
        }

    fun reset() {
        // field = 0    // 오류 — 접근자 밖에서는 쓸 수 없다
        age = 0         // 프로퍼티를 통해야 한다
    }
}
```

## backing property {#backing-property}

backing field로 해결되지 않는 경우가 있습니다. **외부에 노출하는 타입과 내부에서 다루는 타입이 다를 때** 입니다.

```kotlin
class UserRepository {
    private val _users = mutableListOf<User>()      // 내부: 변경 가능
    val users: List<User> get() = _users            // 외부: 읽기 전용
}
```

`_users`가 backing property입니다. 내부에서는 `MutableList`로 자유롭게 조작하고, 외부에는 `List`만 보여 줍니다. backing field는 프로퍼티와 타입이 같아야 하므로 이 구조를 만들 수 없습니다.

Android에서 가장 자주 보는 형태가 이것입니다.

```kotlin
class MainViewModel : ViewModel() {
    private val _uiState = MutableStateFlow<UiState>(UiState.Loading)
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    fun loadData() {
        _uiState.value = UiState.Content("Loaded")   // 내부에서만 변경
    }
}
```

화면 쪽에서는 `viewModel.uiState`를 구독만 할 수 있고 값을 바꿀 수 없습니다. 상태 변경 경로를 ViewModel 안으로 가두는 것이 목적입니다.

## 둘의 차이 {#comparison}

| | backing field | backing property |
|---|---|---|
| 생성 주체 | 컴파일러(암시적) | 개발자(명시적) |
| 접근 방법 | 접근자 안에서 `field` | 일반 프로퍼티처럼 |
| 타입 | 프로퍼티와 **동일** | **다르게** 둘 수 있음 |
| 선언 개수 | 1개(프로퍼티에 종속) | 2개(private + public) |
| 적합한 상황 | 값 가공·검증 | 노출 타입과 내부 타입 분리 |

정리하면 이렇습니다. **저장하는 값 자체는 그대로인데 읽고 쓸 때 로직만 끼우고 싶다면 backing field**, **밖에 보여 줄 타입을 좁히고 싶다면 backing property** 입니다.

## Pro Tips {#pro-tips}

### backing field는 항상 생기지 않는다 {#when-generated}

흔한 오해입니다. backing field는 **필요할 때만** 생성됩니다. 조건은 둘 중 하나입니다.

1. 기본 접근자를 하나라도 사용할 때(초기값을 주는 경우 포함)
2. 커스텀 접근자 안에서 `field`를 참조할 때

둘 다 아니면 필드가 아예 만들어지지 않습니다. 실제로 확인해 보겠습니다.

```kotlin
class C {
    val computed: Int
        get() = 42                      // field 미사용

    var stored: String = "a"
        get() = field.uppercase()       // field 사용
        set(v) { field = v.trim() }
}
```

`javap -p`로 본 결과입니다.

```java
public final class C {
  private java.lang.String stored;      // stored만 필드가 있다
  public final int getComputed();       // computed는 메서드뿐
  public final java.lang.String getStored();
  public final void setStored(java.lang.String);
}
```

`computed`에는 필드가 없습니다. 매번 계산해서 돌려주는 함수일 뿐이므로 저장할 것이 없기 때문입니다. 그래서 **커스텀 getter만 있는 `val`은 메모리를 차지하지 않습니다.** 파생값을 프로퍼티로 노출해도 객체 크기가 늘지 않는다는 뜻입니다.

### 자기 자신을 참조하면 무한 재귀에 빠진다 {#recursion-trap}

`field` 대신 프로퍼티 이름을 쓰면 getter가 자기를 다시 호출합니다.

```kotlin
class D {
    var name: String = "x"
        get() = name        // field가 아니라 name
}
```

컴파일러는 **아무 경고도 주지 않습니다.** Kotlin 2.2.20으로 컴파일하면 오류도 경고도 없이 통과하고, 실행하는 순간 `StackOverflowError`가 납니다.

```
StackOverflowError 발생
```

바이트코드를 보면 `private java.lang.String name;` 필드는 멀쩡히 존재합니다. 초기값 `"x"` 때문에 생성되었지만, getter가 그 필드를 읽지 않고 자기 자신을 부르고 있을 뿐입니다.

> **디버깅 관점** — 프로퍼티에 접근하자마자 `StackOverflowError`가 나고 스택 트레이스에 같은 getter 이름이 반복된다면 이 실수를 먼저 의심하면 됩니다. 로그를 붙이려고 커스텀 getter를 급히 추가할 때 자주 발생합니다.

### 명시적 backing field (Kotlin 2.4) {#explicit-backing-field}

Kotlin 2.4.0에서 [명시적 백킹 필드](https://kotlinlang.org/docs/whatsnew24.html)가 안정화되었습니다. 위에서 본 `_uiState` 패턴을 언어 차원에서 대체하기 위한 기능입니다.

```kotlin
class MainViewModel : ViewModel() {
    val uiState: StateFlow<UiState>
        field = MutableStateFlow(UiState.Loading)

    fun loadData() {
        uiState.value = UiState.Content("Loaded")   // 내부에서는 MutableStateFlow로 보인다
    }
}
```

선언한 클래스 **안에서는** `uiState`가 backing field의 타입(`MutableStateFlow`)으로 해석되어 값을 직접 바꿀 수 있고, **밖에서는** 선언된 타입(`StateFlow`)만 보입니다. 프로퍼티 선언이 절반으로 줄고, `_` 네이밍 관례가 사라지며, 둘 중 잘못된 쪽을 실수로 참조할 위험도 없어집니다.

제약도 있습니다.

- `final val` 프로퍼티에만 사용 가능
- 인터페이스·`abstract`·`expect`·확장 프로퍼티에는 사용 불가
- backing field의 타입은 프로퍼티 선언 타입의 **하위 타입**이어야 함

이 제약을 벗어나거나, 공개 표현과 내부 표현이 실제로 서로 다른 객체여야 하는 경우(`asStateFlow()`처럼 래핑이 필요한 경우)에는 여전히 전통적인 backing property 패턴을 씁니다.

### `_` 접두사는 규칙이 아니라 관례다 {#naming}

`_users`, `_uiState`의 밑줄은 컴파일러가 알아보는 문법이 아닙니다. [Kotlin 코딩 컨벤션](https://kotlinlang.org/docs/coding-conventions.html#names-for-backing-properties)이 권장하는 이름 규칙일 뿐입니다.

의미는 "이건 내부 구현이니 밖에서 쓰지 말라"는 표시입니다. 같은 클래스 안에서는 `_uiState`와 `uiState` 둘 다 보이기 때문에, 표시가 없으면 어느 쪽을 써야 하는지 헷갈립니다. **내부 변경은 `_` 붙은 쪽, 노출은 안 붙은 쪽** 으로 통일해 두면 실수가 줄어듭니다.

## 요약 {#summary}

> **TL;DR** — backing field는 컴파일러가 암시적으로 만들어 주는 저장소로 접근자 안에서 `field`로만 접근하며, 프로퍼티와 타입이 같습니다. backing property는 `_name`처럼 직접 선언하는 별도 프로퍼티로, 노출 타입과 내부 타입을 다르게 가져갈 수 있어 `MutableStateFlow`/`StateFlow` 패턴의 근거가 됩니다. backing field는 기본 접근자를 쓰거나 `field`를 참조할 때만 생성되므로, 커스텀 getter만 있는 `val`은 저장 공간을 차지하지 않습니다.

1. **backing field**: 컴파일러가 암시적으로 생성. 접근자 안에서 `field`로만 접근. 프로퍼티와 타입 동일.
2. **backing property**: 개발자가 명시적으로 선언(`private val _x`). 노출 타입과 내부 타입을 분리할 수 있음.
3. **선택 기준**: 값 가공·검증만 필요하면 backing field, 타입을 좁혀 노출하려면 backing property.
4. **생성 조건**: backing field는 기본 접근자 사용 또는 `field` 참조 시에만 생성. 커스텀 getter만 있는 `val`은 필드 없음.
5. **함정**: 접근자에서 `field` 대신 프로퍼티 이름을 쓰면 무한 재귀. 컴파일 경고 없이 런타임 `StackOverflowError`.
6. **Android 실무**: `private val _uiState = MutableStateFlow(...)` + `val uiState: StateFlow<...>`가 대표 사례.
7. **Kotlin 2.4**: 명시적 백킹 필드(`field = ...`)로 이 패턴을 한 줄로 대체 가능. 단 `final val`에만 적용.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) backing field와 backing property의 차이점은 무엇인가요?">

backing field는 커스텀 접근자에서 `field` 키워드를 사용할 때 컴파일러가 암시적으로 생성하는 저장 공간으로, 해당 프로퍼티에 종속되어 있고 타입도 프로퍼티와 동일합니다. 값을 저장하면서 읽고 쓸 때 가공이나 검증 로직을 끼우고 싶을 때 사용합니다. 반면 backing property는 `private var _age`처럼 개발자가 직접 선언하는 별도 프로퍼티로, 저장소를 공개 프로퍼티와 분리하기 때문에 노출 타입과 내부 타입을 다르게 가져갈 수 있습니다. 내부에서는 `MutableStateFlow`로 다루고 외부에는 `StateFlow`로만 노출하는 패턴이 대표적입니다.

</def>
<def title="Q) backing field는 항상 생성되나요?">

아닙니다. 기본 접근자를 하나라도 사용하거나(초기값을 주는 경우 포함), 커스텀 접근자 안에서 `field`를 참조할 때만 생성됩니다. 두 조건 모두 해당하지 않으면 필드가 만들어지지 않습니다. 예를 들어 `val computed: Int get() = 42`처럼 커스텀 getter만 있고 `field`를 쓰지 않으면 바이트코드에 필드 없이 `getComputed()` 메서드만 생성됩니다. 덕분에 파생값을 프로퍼티로 노출해도 객체의 메모리 크기는 늘어나지 않습니다.

</def>
<def title="Q) 커스텀 getter에서 field 대신 프로퍼티 이름을 쓰면 어떻게 되나요?">

getter가 자기 자신을 재귀 호출하게 되어 `StackOverflowError`가 발생합니다. `var name: String = "x"` 아래에 `get() = name`이라고 쓰면 `name`에 접근할 때 getter가 호출되고, 그 안에서 다시 `name`에 접근하면서 무한히 반복됩니다. 문제는 컴파일러가 오류나 경고를 내지 않는다는 점입니다. 반드시 `field` 키워드를 사용해야 backing field를 직접 읽습니다. 프로퍼티 접근 즉시 `StackOverflowError`가 나고 스택 트레이스에 동일한 getter가 반복된다면 이 실수를 먼저 의심하면 됩니다.

</def>
<def title="Q) ViewModel에서 _uiState와 uiState를 나누는 이유는 무엇인가요?">

상태 변경 경로를 ViewModel 내부로 제한하기 위해서입니다. `private val _uiState = MutableStateFlow(...)`는 값을 변경할 수 있는 타입이지만 `private`이라 밖에서 접근할 수 없고, `val uiState: StateFlow<...> = _uiState.asStateFlow()`는 읽기 전용 타입으로 노출됩니다. 화면 쪽에서는 구독만 가능하고 임의로 상태를 바꿀 수 없으므로 단방향 데이터 흐름(UDF)이 지켜집니다. 밑줄 접두사는 컴파일러 문법이 아니라 Kotlin 코딩 컨벤션의 이름 규칙이며, 같은 클래스 안에서 둘 다 보이기 때문에 어느 쪽을 써야 하는지 구분하는 표시 역할을 합니다.

</def>
<def title="Q) Kotlin 2.4의 명시적 백킹 필드는 무엇인가요?">

backing property 패턴을 언어 차원에서 대체하기 위해 도입된 기능으로, `val uiState: StateFlow<UiState>` 아래에 `field = MutableStateFlow(UiState.Loading)`처럼 백킹 필드를 직접 선언합니다. 선언한 클래스 내부에서는 프로퍼티 참조가 백킹 필드의 타입(`MutableStateFlow`)으로 해석되어 값을 변경할 수 있고, 외부 호출자에게는 선언된 타입(`StateFlow`)만 보여 캡슐화가 유지됩니다. 선언이 절반으로 줄고 `_` 네이밍 관례도 사라집니다. 다만 `final val` 프로퍼티에만 쓸 수 있고 인터페이스·추상·expect·확장 프로퍼티에는 사용할 수 없으며, 백킹 필드 타입은 선언 타입의 하위 타입이어야 합니다.

</def>
</deflist>
