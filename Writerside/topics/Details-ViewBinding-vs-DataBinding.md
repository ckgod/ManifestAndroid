# Details: ViewBinding vs DataBinding

## ViewBinding과 DataBinding의 차이점은 무엇인가요? {#viewbinding-vs-databinding}

ViewBinding과 DataBinding은 모두 Android에서 View 작업 시 보일러플레이트 코드를 줄이기 위해 제공되는 도구입니다. 그러나 목적과 기능이 다르므로, 프로젝트의 요구 사항에 따라 적절한 도구를 선택하는 것이 중요합니다.

### ViewBinding 특징 {#viewbinding-characteristics}

ViewBinding은 `findViewById()` 없이 레이아웃의 View에 접근하는 과정을 단순화하기 위해 도입된 기능입니다. 각 XML 레이아웃 파일에 대한 바인딩 클래스를 생성하며, ID가 있는 모든 View에 대한 직접 참조를 제공합니다.

**핵심 특징:**

- XML 레이아웃 파일에 대한 바인딩 클래스를 자동 생성합니다.
- `findViewById()` 없이 레이아웃 내 View를 직접 참조할 수 있습니다.
- nullable 및 타입에 대한 컴파일 타임 검사로 타입 안전성을 보장합니다.
- 바인딩 표현식이나 데이터 기반 업데이트 같은 고급 기능은 지원하지 않습니다.

```kotlin
// ViewBinding 사용 예시
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
{title="ViewBindingExample.kt"}

### DataBinding 특징 {#databinding-characteristics}

DataBinding은 UI 컴포넌트를 데이터 소스에 직접 바인딩할 수 있는 더 복잡하고 유연한 라이브러리입니다. 바인딩 표현식, 옵저버블 데이터, 양방향 데이터 바인딩을 지원하여 MVVM 아키텍처 구현에 적합합니다.

**핵심 특징:**

- XML에서 UI 요소를 데이터 소스에 직접 바인딩할 수 있습니다.
- UI 컴포넌트를 동적으로 업데이트하는 바인딩 표현식을 지원합니다.
- UI와 데이터 간 실시간 동기화를 위한 양방향 데이터 바인딩을 제공합니다.
- LiveData 및 StateFlow와의 생명주기 인식 옵저버블 데이터 통합을 지원합니다.

```kotlin
// DataBinding 사용 예시
class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val binding: ActivityMainBinding =
            DataBindingUtil.setContentView(this, R.layout.activity_main)

        binding.lifecycleOwner = this
        binding.viewModel = ViewModelProvider(this)[MainViewModel::class.java]
    }
}
```
{title="DataBindingExample.kt"}

### 주요 차이점 {#key-differences}

| 항목 | ViewBinding | DataBinding |
|------|-------------|-------------|
| 목적 | View 접근 단순화 | 고급 데이터 기반 UI 바인딩 |
| 생성 클래스 | View 직접 참조 | View 참조 + 데이터 바인딩 기능 |
| XML 표현식 | 미지원 | `@{}`, `@={}` 지원 |
| 양방향 바인딩 | 미지원 | 지원 |
| 성능 | 빠름, 오버헤드 최소 | 데이터 바인딩 로직으로 인한 오버헤드 |
| `<layout>` 태그 | 불필요 | 필수 |
| LiveData 연동 | 미지원 | 지원 |

1. **목적**: ViewBinding은 View 접근을 단순화하고, DataBinding은 고급 데이터 기반 UI 바인딩을 지원합니다.
2. **생성 클래스**: ViewBinding은 View에 대한 직접 참조만 생성합니다. DataBinding은 View 참조뿐 아니라 데이터 바인딩 기능이 내장된 추가 클래스도 생성합니다.
3. **표현식**: ViewBinding은 XML 표현식을 지원하지 않지만, DataBinding은 바인딩 표현식과 동적 데이터 바인딩을 지원합니다.
4. **양방향 바인딩**: DataBinding만 양방향 바인딩을 지원합니다.
5. **성능**: ViewBinding은 데이터 바인딩 로직을 처리하지 않아 더 빠르고 오버헤드가 적습니다.

### 요약 {#summary}

<tldr>
`findViewById()` 없는 단순 View 참조가 필요한 경우, 특히 소규모 프로젝트에서는 ViewBinding을 사용하세요. 복잡한 데이터 기반 UI나 MVVM 아키텍처 작업 시에는 동적 바인딩 기능과 LiveData, StateFlow, `@Bindable` 어노테이션이 적용된 옵저버블 속성과의 뛰어난 통합성을 제공하는 DataBinding을 선택하세요. DataBinding이 더 다재다능하지만, ViewBinding으로 충분한 단순한 사용 사례에는 그 추가 오버헤드가 불필요할 수 있습니다.
</tldr>

<deflist collapsible="true" default-state="collapsed">
<def title="Q) DataBinding의 @Bindable 어노테이션은 어떻게 동작하며, 양방향 바인딩과 어떤 관계인가요?">

`@Bindable` 어노테이션은 `BaseObservable`을 상속한 클래스에서 사용하며, 특정 필드가 변경될 때 UI를 업데이트하도록 DataBinding에 알립니다.

```kotlin
class User : BaseObservable() {
    @get:Bindable
    var name: String = ""
        set(value) {
            field = value
            notifyPropertyChanged(BR.name) // BR은 DataBinding이 자동 생성
        }
}
```
{title="ObservableUser.kt"}

양방향 바인딩(`@={}`)과 함께 사용하면 사용자 입력이 `name` 필드를 업데이트하고, 코드에서 `name`을 변경하면 `notifyPropertyChanged()`를 통해 UI가 자동으로 반영됩니다. 단, LiveData나 StateFlow를 사용하면 `@Bindable` 없이도 동일한 반응성을 얻을 수 있어 현대 Android 개발에서는 LiveData/StateFlow 방식이 더 권장됩니다.

</def>
</deflist>
