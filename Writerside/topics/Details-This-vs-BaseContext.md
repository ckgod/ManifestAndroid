# Details: This vs BaseContext

## Activity의 `this`와 `baseContext`는 무엇이 다른가?
Activity에서 `this`와 `baseContext`는 모두 컨텍스트에 대한 액세스를 제공하지만 서로 다른 용도로 사용되며 안드로이드 컨텍스트 계층 구조의 다른 수준을 나타낸다.
코드에서 혼동이나 잠재적인 문제를 피하려면 각각의 사용 시기를 아는 것이 중요하다.

### Activity에서 `this`
Activity에서 `this` 키워드는 Activity 클래스의 현재 인스턴스를 나타낸다.
Activity는 `ContextWrapper`의 하위 클래스 이므로(따라서 간접적으로 Context의 하위 클래스), 생명 주기 관리 및 UI와의 상호 작용과 같은 추가 기능을 포함하여 Activity의 특정 컨텍스트에 대한 액세스를 제공한다.

Activity에서 `this`를 사용하면 Activity의 현재 컨텍스트를 가리키는 경우가 많으므로 해당 Activity와 관련된 메서드를 호출할 수 있다.
예를 들어 다른 Activity를 시작하거나 특정 Activity와 연결된 Dialog를 보여줘야 할 때 `this`를 사용할 수 있다.

```Kotlin
val intent = Intent(this, AnotherActivity::class.java)
startActivity(intent)

val dialog = AlertDialog.Builder(this)
    .setTitle("Example")
    .setMessage("This dialog is tied to this Activity instance")
    .show()
```

### Activity에서 `baseContext`
`baseContext`는 Activity가 구축되는 순수 Context를 나타낸다.
안드로이드 시스템이 Activity를 만들 때 기본으로 제공해 주는 Context이며, Activity의 테마 정보 등은 포함되어 있지 않다.
일반적으로 `Context`메서드의 핵심 구현을 제공하는 `ContextImpl`인스턴스이다.

`baseContext`는 보통 `getBaseContext()`메서드를 통해 액세스할 수 있다.
직접 사용하는 경우는 거의 없지만 Custom `ContextWrapper`를 구현하거나 래핑된 Context 뒤에 있는 원본 Context를 참조해야 할 때 유용하게 사용할 수 있다.

```Kotlin
val systemService = baseContext.getSystemService(Context.LAYOUT_INFLATER_SERVICE)
```

### `this`와 `baseContext`의 주요 차이점
1. 범위: `this`는 현재 Activity의 인스턴스 자체와 그 생명 주기를 나타내며, `baseContext`는 Activity가 빌드되는 하위 수준 `Context`를 나타낸다.
2. 사용처: `this`는 주로 다른 액티비티를 시작하거나 다이얼로그를 표시하는 것처럼 `Activity`의 생명주기나 UI와 밀집하게 관련된 작업에 사용된다. `baseContext`는 일반적으로 커스텀 `ContextWrapper`를 구현하는 경우처럼 `Context`의 핵심 구현과 상호작용할 때 사용된다.
3. 계층: `baseContext`는 `Activity`의 근본이 되는 컨텍스트이다. `baseContext`에 직접 접근하면, `Activity`가 `ContextWrapper`로서 제공하는 추가적인 기능(예: 테마)을 건너뛰게 된다.

### 예시: 특정 시스템 서비스만 다르게 동작시키기
아래 코드는 `LayoutInflater`라는 시스템 서비스를 요청할 때만 우리가 만든 커스텀 객체를 돌려주고, 나머지 모든 서비스 요청은 원래 `Context`가 하던 대로 처리하도록 만드는 예제이다.

```Kotlin
class MyCustomContext(base: Context) : ContextWrapper(base) {

    private val myLayoutInflater: MyLayoutInflater by lazy {
        MyLayoutInflater(base)
    }

    override fun getSystemService(name: String): Any? {
        if (Context.LAYOUT_INFLATER_SERVICE == name) {
            return myLayoutInflater
        }

        return baseContext.getSystemService(name)
    }
}
```

### 요약

`Activity`에서 `this`는 현재 액티비티 인스턴스 자체를 가리키며, 생명주기 및 UI 관련 기능을 갖춘 상위 수준의 컨텍스트를 제공한다.
반면, `baseContext`는 액티비티의 기반이 되는 근본적인 컨텍스트를 나타내며, 주로 커스텀 `ContextWrapper` 구현과 같은 고급 시나리오에서 사용된다.
안드로이드 개발에서는 대부분 `this`를 사용하지만, `baseContext`를 이해하면 디버깅을 하거나 모듈화되고 재사용 가능한 컴포넌트를 만드는 데 도움이 된다.
