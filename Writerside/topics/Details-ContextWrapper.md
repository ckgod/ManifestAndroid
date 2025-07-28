# Details: ContextWrapper

## ContextWrapper란 무엇인가요?
`ContextWrapper`는 안드로이드 기본 클래스로, `Context`객체를 래핑하여 래핑된 `Context`에 호출을 위임하는 기능을 제공한다.
주된 목적은 기존 `Context`의 동작을 직접 수정하지 않으면서, 기능을 추가하거나 일부 동작을 변경하는 것이다.

### ContextWrapper의 목적 {#purpose-context-wrapper}
`ContextWrapper`는 기존 Context의 특정 동작을 변경하거나 새로운 기능을 추가할 수 있다. 
- 기능 확장: 원래 `Context`에 없는 새로운 기능을 추가할 수 있다.
- 기능 변경: `getSystemService()`와 같은 `Context`의 특정 메서드가 다르게 동작하도록 재정의(override)할 수 있다.

### 사용 사례
- 커스텀 Context: 개발자가 특정 상황에 맞는 `Context`를 만들어야 할 때 유용하다. 예를 들어, 특정 액티비티나 뷰 그룹에서만 글꼴이나 테마를 다르게 적용하고 싶을 때, `getSystemService()`를 재정의한 커스텀 `ContextWrapper`를 만들어 사용할 수 있다.
- 동적 리소스 처리: `Context`를 래핑하여 strings, dimens, styles와 같은 리소스를 동적으로 제공하거나 수정한다.
- 의존성 주입: Dagger 및 Hilt와 같은 라이브러리는 ContextWrapper를 생성하여 의존성 주입을 위해 구성 요소에 사용자 지정 컨텍스트를 연결합니다.

### 예제

#### ContextWrapper를 사용하여 사용자 정의 테마를 적용 {#example-context-wrapper-custom}
```Kotlin
class CustomThemeContextWrapper(base: Context): ContextWrapper(base) {
    override fun getTheme(): Resources.Theme {
        val theme = super.getTheme()
        theme.applyStyle(R.style.CustomTheme, true)
        return theme
    }
}
```

#### Activity에서 custom wrapper 사용
```Kotlin
class MyActivity : AppCompatActivity() {
    override fun attachBaseContext(newBase: Context) {
        super.attachBaseContext(CustomThemeContextWrapper(newBase))
    }
}
```

### ContextWrapper 사용의 이점 {#benefit-context-wrapper}
- 재사용성: 래퍼 클래스에 사용자 정의 로직을 캡슐화하여 여러 컴포넌트에서 재사용할 수 있다.
- 캡슐화: 원래의 컨텍스트 구현을 변경하지 않고 동작을 개선하거나 수정할 수 있다.
- 호환성: 기존의 모든 `Context` 객체와 매끄럽게 작동하며, 하위 호환성을 유지한다.

### 요약
ContextWrapper는 안드로이드에서 `Context`동작을 커스터마이징하기 위한 유연하고 재사용 가능한 도구이다. 
개발자가 직접 변경하지 않고도 원래 `Context`에 대한 동작을 가로채고 수정할 수 있으므로 모듈식 적응형 애플리케이션을 구축하는 데 필수적인 클래스이다.