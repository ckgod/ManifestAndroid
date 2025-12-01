# Q35) ViewStub

## `ViewStub`을 사용해 본 적이 있습니까? `ViewStub`을 사용하여 `UI` 성능을 어떻게 최적화합니까?

`ViewStub`은 Android 공식 문서에서 "zero-sized invisible view"로 정의되며, 레이아웃의 지연 로딩(lazy loading)을 위한 경량 뷰입니다.

앱 실행 시점에 당장 필요 없는 뷰의 생성을 뒤로 미룸으로써, 불필요한 메모리 낭비를 막고 렌더링 성능을 최적화하는 데 사용됩니다.

### `ViewStub`의 주요 특징 {#VS1}

1.  **경량 (Lightweight)**: `ViewStub`은 인플레이션되기 전까지 레이아웃 공간을 차지하거나 리소스를 소비하지 않으므로 메모리 점유율이 최소화된 매우 가벼운 뷰입니다.
2.  **지연된 인플레이션 (Delayed Inflation)**: `ViewStub`에 지정된 실제 레이아웃은 `inflate()` 메서드가 호출되거나 `ViewStub`이 보이게 될 때만 인플레이션됩니다.
3.  **일회성 사용 (One-Time Use)**: 일단 인플레이션되면 `ViewStub`은 뷰 계층에서 인플레이션된 레이아웃으로 대체되며 재사용할 수 없습니다.

### `ViewStub`의 일반적인 사용 사례 {#VS2}

1.  **조건부 레이아웃 (Conditional Layouts)**: `ViewStub`은 오류 메시지, 진행률 표시줄 또는 선택적 `UI` 요소와 같이 조건부로 표시되는 레이아웃에 이상적입니다.
2.  **초기 로드 시간 단축 (Reducing Initial Load Time)**: 복잡하거나 리소스 집약적인 뷰의 인플레이션을 지연함으로써 `ViewStub`은 `Activity` 또는 `Fragment`의 초기 렌더링 시간을 개선하는 데 도움이 됩니다.
3.  **동적 `UI` 요소 (Dynamic UI Elements)**: 필요할 때만 화면에 동적 콘텐츠를 추가하는 데 사용할 수 있어 메모리 사용량을 최적화합니다.

### `ViewStub` 사용 방법  {#VS3}

`ViewStub`은 인플레이션해야 할 레이아웃 리소스를 가리키는 속성과 함께 `XML` 레이아웃에 정의됩니다.

#### `activity_main.xml`
```xml
<LinearLayout
    xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical">

    <!-- Regular Views -->
    <TextView
        android:id="@+id/title"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="Main Content" />

    <!-- Placeholder ViewStub -->
    <ViewStub
        android:id="@+id/viewStub"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:layout="@layout/optional_content" />
</LinearLayout>
```

#### `ViewStub` 인플레이션하기 {#VS5}
```kotlin
class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val viewStub = findViewById<ViewStub>(R.id.viewStub)

        // Inflate the layout when needed
        val inflatedView = viewStub.inflate()

        // Access views from the inflated layout
        val optionalTextView = inflatedView.findViewById<TextView>(R.id.optionalText)
        optionalTextView.text = "Inflated Content"
    }
}
```

### `ViewStub`의 장점 {#VS53}

1.  **최적화된 성능 (Optimized Performance)**: 항상 표시되지 않을 수 있는 뷰의 생성을 지연하여 메모리 사용량을 줄이고 초기 렌더링 성능을 향상시킵니다.
2.  **단순화된 레이아웃 관리 (Simplified Layout Management)**: 뷰를 프로그래밍 방식으로 수동으로 추가하거나 제거할 필요 없이 선택적 `UI` 요소를 쉽게 관리할 수 있습니다.
3.  **사용 용이성 (Ease of Use)**: 직관적인 `API`와 `XML` 통합 덕분에 `ViewStub`은 개발자에게 편리한 도구입니다.

### `ViewStub`의 한계 {#VS2465}

1.  **일회성 사용 (Single-Use)**: 일단 인플레이션되면 `ViewStub`은 뷰 계층에서 제거되며 재사용할 수 없습니다.
2.  **제한된 제어 (Limited Control)**: 플레이스홀더이므로 인플레이션되기 전까지는 사용자 상호작용을 처리하거나 복잡한 작업을 수행할 수 없습니다.

### 요약

`ViewStub`은 필요할 때까지 레이아웃 인플레이션을 지연시켜 성능을 최적화하는 `Android`의 유용한 도구입니다. 특히 조건부 레이아웃이나 항상 필요하지 않을 수 있는 뷰에 유용하며, 메모리 사용량을 줄이고 앱 응답성을 향상시키는 데 도움이 됩니다. `ViewStub`을 적절하게 사용하면 더욱 효율적이고 간소화된 사용자 경험을 얻을 수 있습니다.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) ViewStub이 인플레이션될 때 무슨 일이 발생하며, 레이아웃 성능 및 메모리 사용량 측면에서 뷰 계층에 어떤 영향을 미칩니까?">
`ViewStub`의 인플레이션이 호출되면, ViewStub 자신을 부모 ViewGroup에서 제거하고, 지정된 layout을 인플레이트하고 같은 위치에 새로운 View를 삽입하게 됩니다. 
한 번 인플레이트되면 ViewStub은 뷰 계층에서 완전히 사라집니다. 다시 사용할 수 없습니다.

ViewStub은 초기 레이아웃 성능을 개선시킵니다. 크기가 0이므로 measure, layout, draw 단계를 건너뜁니다. 

ViewStub은 View를 상속하지만 매우 가벼운 구조입니다. 인플레이션 전에는 뷰 계층 깊이도 감소됩니다.

```plain text
// ViewStub.java 주요 필드
public class ViewStub extends View {
private int mInflatedId;
private int mLayoutResource;
private WeakReference<View> mInflatedViewRef;
// ... 최소한의 필드만 보유
}

ViewStub은 View를 상속하지만 매우 가벼운 구조입니다:
- 실제 View 객체: 약 1-2KB (기본 필드 포함)
- ViewStub: 약 200-400 bytes
- 복잡한 레이아웃: 수십 개의 View × 각 1-2KB = 수십 KB

뷰 계층 구조에 미치는 영향

인플레이션 전:
ViewGroup (depth=0)
└── ViewStub (depth=1, size=0x0)

인플레이션 후:
ViewGroup (depth=0)
└── ConstraintLayout (depth=1)
├── TextView (depth=2)
├── ImageView (depth=2)
└── RecyclerView (depth=2)
└── ... (depth=3+)
```

</def>
</deflist>