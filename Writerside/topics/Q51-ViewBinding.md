# Q51) ViewBinding

## ViewBinding을 사용할 때의 장점은 무엇인가요? {#what-is-viewbinding}

`ViewBinding`은 레이아웃의 View와 상호작용하는 과정을 단순화하기 위해 Android에 도입된 기능입니다. `findViewById()` 호출 없이 타입 안전한 방식으로 View에 직접 접근할 수 있어 보일러플레이트 코드를 줄이고 잠재적인 런타임 오류를 최소화합니다.

### ViewBinding 동작 방식 {#how-viewbinding-works}

ViewBinding을 프로젝트에서 활성화하면 Android가 각 XML 레이아웃 파일에 대한 바인딩 클래스를 자동으로 생성합니다. 생성된 클래스 이름은 레이아웃 파일명을 기반으로 하며, 언더스코어(`_`)를 카멜 케이스로 변환하고 `Binding`을 뒤에 붙입니다. 예를 들어 `activity_main.xml`에 대해서는 `ActivityMainBinding` 클래스가 생성됩니다.

바인딩 클래스는 레이아웃 내 모든 View에 대한 참조를 포함하므로, 캐스팅이나 `findViewById()` 없이 직접 View에 접근할 수 있습니다.

```kotlin
class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.textView.text = "Hello, ViewBinding!"
    }
}
```
{title="ViewBinding.kt"}

`inflate()` 메서드로 바인딩 클래스 인스턴스를 생성하고, `binding.root`를 `setContentView()`에 전달하여 레이아웃을 설정합니다.

### ViewBinding 활성화 방법 {#enabling-viewbinding}

`build.gradle` 파일에 다음을 추가하면 ViewBinding을 활성화할 수 있습니다.

```kotlin
android {
    viewBinding {
        enabled = true
    }
}
```
{title="build.gradle.kts"}

활성화하면 프로젝트의 모든 XML 레이아웃에 대한 바인딩 클래스가 자동으로 생성됩니다.

### ViewBinding의 장점 {#advantages-of-viewbinding}

- **타입 안전성**: View에 직접 접근하여 캐스팅이 필요 없으므로, 타입 불일치로 인한 런타임 오류가 발생하지 않습니다.
- **간결한 코드**: `findViewById()` 호출이 불필요해져 보일러플레이트 코드가 크게 줄어듭니다.
- **Null 안전성**: 선택적 UI 컴포넌트와 상호작용할 때 nullable View를 자동으로 처리하여 더 안전한 코드를 작성할 수 있습니다.
- **성능**: DataBinding과 달리 바인딩 표현식이나 추가 XML 파싱을 사용하지 않아 런타임 오버헤드가 최소화됩니다.

### DataBinding과의 비교 {#comparison-with-databinding}

DataBinding은 바인딩 표현식, 양방향 데이터 바인딩 등 더 많은 기능을 제공하지만 복잡성이 높고 런타임 오버헤드가 있습니다. ViewBinding은 View 상호작용을 단순화하는 데만 집중하며 훨씬 가볍습니다. LiveData 바인딩 같은 고급 기능이 필요하지 않을 때는 ViewBinding이 이상적인 선택입니다.

| 항목 | ViewBinding | DataBinding |
|------|-------------|-------------|
| 설정 복잡도 | 낮음 | 높음 |
| 런타임 오버헤드 | 최소 | 있음 |
| 바인딩 표현식 | 미지원 | 지원 |
| 양방향 바인딩 | 미지원 | 지원 |
| 적합한 상황 | 단순 View 접근 | LiveData 연동, MVVM |

### ViewBinding 이전: ButterKnife {#before-viewbinding-butterknife}

ViewBinding이 공식적으로 지원되기 전, Android 생태계에서는 **ButterKnife** 라이브러리가 `findViewById()` 없이 View에 접근하는 방법으로 널리 사용되었습니다. ButterKnife는 어노테이션 처리(Annotation Processing)를 통해 View 인스턴스를 필드에 주입하는 방식으로 타입 안전성을 제공했습니다. Jake Wharton의 명성을 확립하는 데 기여한 프로젝트 중 하나로, Android 개발에 상당한 변화와 창의성을 불어넣었습니다. ViewBinding의 공식 도입으로 현재는 deprecated되었지만, 의존성 주입 패턴에 관심 있는 개발자라면 살펴볼 가치가 있는 혁신적인 솔루션이었습니다.

### 요약 {#summary}

<tldr>
ViewBinding은 Android에서 View와 상호작용하는 가볍고 타입 안전한 방법입니다. `findViewById()` 대비 보일러플레이트를 줄이고 런타임 안전성을 높이며, DataBinding의 고급 기능이 필요 없는 경우에 탁월한 선택입니다.
</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) ViewBinding이 findViewById()와 비교하여 타입 안전성과 Null 안전성을 어떻게 개선하나요?">

**타입 안전성**

`findViewById()`는 `View`를 반환하므로 개발자가 원하는 타입으로 직접 캐스팅해야 합니다. 이때 잘못된 타입으로 캐스팅하면 `ClassCastException`이 런타임에 발생합니다.

```kotlin
// 타입 캐스팅 오류 가능성
val button = findViewById<Button>(R.id.textView) // 런타임 오류 위험
```

반면 ViewBinding은 각 View에 대해 이미 올바른 타입으로 선언된 참조를 제공하므로 캐스팅이 필요 없고, 타입 불일치는 컴파일 타임에 감지됩니다.

**Null 안전성**

`findViewById()`는 해당 ID가 현재 레이아웃에 없으면 `null`을 반환하는데, 이를 처리하지 않으면 `NullPointerException`이 발생합니다. ViewBinding은 레이아웃에 존재하는 View는 non-null 타입으로, 일부 구성(예: 화면 방향별)에서만 존재하는 View는 nullable 타입으로 자동 처리합니다. 이를 통해 런타임 null 관련 충돌을 사전에 방지할 수 있습니다.

</def>
</deflist>
