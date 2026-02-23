# Q49) AppCompat

## AppCompat 라이브러리란 무엇인가요? {#what-is-appcompat}

[AppCompat 라이브러리](https://developer.android.com/jetpack/androidx/releases/appcompat)는 Android Jetpack 제품군의 일부로, **이전 버전의 Android와의 호환성을 유지하면서** 최신 기능과 디자인 패턴을 구현할 수 있도록 도와줍니다. 다양한 Android 버전을 사용하는 폭넓은 기기를 타겟으로 하는 개발자에게 특히 유용한 라이브러리입니다.

### 주요 기능 {#key-features}

**UI 컴포넌트 하위 호환성**

AppCompat은 `AppCompatActivity`와 같은 최신 UI 컴포넌트를 도입합니다. `AppCompatActivity`는 `FragmentActivity`를 확장하여 구버전 Android에서도 액션 바 같은 기능을 사용할 수 있도록 보장합니다.

**Material Design 지원**

AppCompat을 사용하면 구버전 Android 기기에서도 Material Design 원칙을 적용할 수 있습니다. `AppCompatButton`, `AppCompatTextView` 등의 위젯은 기기의 API 레벨에 따라 자동으로 외형과 동작을 조정합니다.

**테마 및 스타일 지원**

`Theme.AppCompat` 테마를 사용하면 모든 API 레벨에서 일관된 외형을 보장합니다. 구버전 Android에서도 벡터 드로어블 지원 같은 최신 스타일링 기능을 사용할 수 있습니다.

**동적 기능 지원**

동적 리소스 로딩과 벡터 드로어블 지원을 통해, 하위 호환성을 유지하면서 최신 디자인 요소를 효율적으로 구현할 수 있습니다.

### AppCompat을 사용해야 하는 이유 {#why-use-appcompat}

AppCompat 라이브러리를 사용하는 주된 이유는 최신 Android 기능과 UI 컴포넌트가 지원하는 모든 API 레벨에서 일관되게 동작하도록 보장하기 위해서입니다. 구버전 Android를 실행하는 기기에 대한 호환성 유지 복잡성을 줄이면서, 최신 기능이 풍부한 앱을 개발하는 데 집중할 수 있습니다.

### AppCompatActivity 사용 예시 {#appcompat-activity-example}

```kotlin
//import androidx.appcompat.app.AppCompatActivity
//import android.os.Bundle

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
    }
}
```
{title="MainActivity.kt"}

`AppCompatActivity`를 상속함으로써 구버전 Android 기기에서도 액션 바를 비롯한 다양한 최신 기능을 활용할 수 있습니다.

### 요약 {#summary}

<tldr>
AppCompat 라이브러리는 광범위한 기기와 API 레벨과 호환되는 Android 앱을 빌드하는 데 유용합니다. 하위 호환 컴포넌트, Material Design 지원, 일관된 테마를 제공함으로써 개발을 단순화하고 구버전 기기에서의 사용자 경험을 향상시킵니다.
</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) AppCompat 라이브러리가 구버전 Android에서 Material Design을 지원하는 방법과, 이 혜택을 받는 주요 UI 컴포넌트는 무엇인가요?">

AppCompat은 Material Design 위젯의 하위 호환 버전을 제공하는 방식으로 구버전 Android에서 Material Design을 지원합니다. 기기의 API 레벨을 감지하여 가능한 경우 네이티브 구현을 사용하고, 그렇지 않으면 자체 백포트(backport) 구현으로 대체합니다.

주요 혜택을 받는 UI 컴포넌트는 다음과 같습니다.

- **AppCompatButton**: Material Design 스타일의 버튼으로, 구버전에서도 리플 효과와 상태별 색상 변화를 지원합니다.
- **AppCompatTextView**: 폰트 패밀리, 텍스트 외형 등 최신 텍스트 스타일링 기능을 하위 호환합니다.
- **AppCompatImageView**: 벡터 드로어블과 틴트(tint) 지원을 백포트합니다.
- **AppCompatCheckBox / AppCompatRadioButton**: Material Design 스타일의 선택 컴포넌트를 구버전에서도 동일하게 표시합니다.
- **Toolbar**: 구버전 Android에서 ActionBar를 대체하는 유연한 상단 바로, Material Design 가이드라인을 따릅니다.

이를 통해 개발자는 API 레벨별 분기 코드 없이도 일관된 Material Design UI를 구현할 수 있습니다.

</def>
</deflist>
