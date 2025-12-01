# Q36) Custom View

## Custom View 구현 방법

Custom View를 구현하는 것은 여러 화면에서 재사용해야 하는 특정 모양과 동작을 가진 UI 구성 요소를 설계할 때 필수적입니다.
Custom View를 사용하면 개발자는 시각적 표현과 상호 작용 로직을 모두 맞춤 설정할 수 있으며, 애플리케이션 전체의 일관성과 유지 관리성을 보장할 수 있습니다.
Custom View를 생성함으로써 복잡한 UI 로직을 캡슐화하고, 재사용성을 높이며, 프로젝트 내 다양한 계층의 구조를 단순화할 수 있습니다.

애플리케이션이 표준 UI 구성 요소로는 구현할 수 없는 고유한 디자인 요소를 요구한다면, Custom View 구현이 필수적입니다.
Android 개발에서는 다음 단계에 따라 XML을 사용하여 Custom View를 생성할 수 있습니다.

### 1. Custom View 클래스 생성

먼저, 기본 View 클래스(예: `View`, `ImageView`, `TextView` 등)를 확장하는 새 클래스를 정의합니다. 
그런 다음 아래 예시에서 보듯이, 구현하려는 Custom 동작에 따라 필요한 생성자와 `onDraw()`, `onMeasure()`, `onLayout()`과 같은 메서드를 오버라이드합니다.

```kotlin
class CustomCircleView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyle: Int = 0
) : View(context, attrs, defStyle) {

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        val paint = Paint().apply {
            color = Color.RED
            style = Paint.Style.FILL
        }
        // Draw a red circle at the center
        canvas.drawCircle(width / 2f, height / 2f, width / 4f, paint)
    }
}
```

### 2. XML 레이아웃에서 Custom View 사용

Custom View 클래스를 생성한 후, XML 레이아웃 파일에서 직접 참조할 수 있습니다. 
Custom 클래스의 전체 패키지 이름을 XML 태그로 사용해야 합니다. 다음 예시와 같이 XML에서 정의할 수 있는 Custom 속성을 Custom View에 전달할 수도 있습니다(다음 단계 참조).

```xml

<com.example.CustomCircleView
        android:layout_width="100dp"
        android:layout_height="100dp"
        android:layout_gravity="center"/>
```

### 3. Custom 속성 추가 (선택 사항)

`res/values` 폴더에 새 `attrs.xml` 파일에 Custom 속성을 정의합니다. 
이렇게 하면 아래 코드와 같이 XML 레이아웃에서 View의 속성을 Custom화할 수 있습니다.

```xml
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <declare-styleable name="CustomCircleView">
        <attr name="circleColor" format="color"/>
        <attr name="circleRadius" format="dimension"/>
    </declare-styleable>
</resources>
```

Custom View 클래스에서는 아래 코드와 같이 생성자 내에서 `context.obtainStyledAttributes()`를 사용하여 Custom 속성을 검색합니다.

```kotlin
class CustomCircleView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyle: Int = 0
) : View(context, attrs, defStyle) {

    var circleColor: Int = Color.RED
    var circleRadius: Float = 50f

    init {
        when {
            attrs != null && defStyle != 0 -> getAttrs(attrs, defStyle)
            attrs != null -> getAttrs(attrs)
        }
    }

    private fun getAttrs(attrs: AttributeSet) {
        val typedArray = context.obtainStyledAttributes(attrs, R.styleable.CustomCircleView)
        try {
            setTypeArray(typedArray)
        } finally {
            typedArray.recycle()
        }
    }

    private fun getAttrs(attrs: AttributeSet, defStyle: Int) {
        val typedArray = context.obtainStyledAttributes(attrs, R.styleable.CustomCircleView, defStyle, 0)
        try {
            setTypeArray(typedArray)
        } finally {
            typedArray.recycle()
        }
    }

    private fun setTypeArray(typedArray: TypedArray) {
        circleColor = typedArray.getColor(R.styleable.CustomCircleView_circleColor, Color.RED)
        circleRadius = typedArray.getDimension(R.styleable.CustomCircleView_circleRadius, 50f)
    }
}
```

이제 XML 파일에서 Custom 속성을 사용할 수 있습니다.

```xml
<com.example.CustomCircleView
        android:layout_width="100dp"
        android:layout_height="100dp"
        app:circleColor="@color/blue"
        app:circleRadius="30dp"/>
```

### 4. 레이아웃 측정 처리 (선택 사항)

Custom View가 표준 View와 다르게 동작하는 경우, 특히 Custom View의 크기를 측정하는 방식을 제어하려면 `onMeasure()` 메서드를 오버라이드합니다.

아래 예시를 참조하세요.

```kotlin
override fun onMeasure(widthMeasureSpec: Int, heightMeasureSpec: Int) {
    val desiredSize = 200
    val width = resolveSize(desiredSize, widthMeasureSpec)
    val height = resolveSize(desiredSize, heightMeasureSpec)
    setMeasuredDimension(width, height)
}
```

> Custom View를 생성하는 것은 애플리케이션의 요구 사항 또는 특정 디자인 사양에 맞춰 재사용 가능한 특수 구성 요소가 필요할 때 필수적입니다. 
> Custom View는 기능과 사용자 경험을 향상시키기 위해 애니메이션, callbacks, custom attributes 및 기타 고급 기능을 통합할 수 있습니다. 
> Custom View 구축에 대한 이해를 심화하려면 GitHub에서 제공되는 다양한 예제 및 구현을 살펴보는 것을 고려해 보세요. 
> 
> 실제 사용 사례를 관찰하는 것은 귀중한 통찰력과 영감을 제공할 수 있습니다. 
> Custom View 구현의 실제 예는 [GitHub의 ElasticViews](https://github.com/skydoves/ElasticViews)와 [GitHub의 ProgressView](https://github.com/skydoves/ProgressView)를 참조하십시오. 
> 이 프로젝트들은 재사용 가능하고 동적인 Custom View를 생성하는 실용적인 접근 방식을 보여줍니다.
> 또한 [GitHub의 CircleImageView](https://github.com/hdodenhof/CircleImageView)를 살펴보는 것도 가치가 있습니다.

### 요약

XML을 통해 Android에서 Custom View를 구현하면 UI 디자인에 유연성을 제공합니다.
Custom View 시스템과 [Canvas](https://developer.android.com/reference/android/graphics/Canvas)를 사용하여 다양한 Custom 위젯을 생성할 수 있습니다.
더 자세한 내용은 [Custom View에 대한 Android 개발자 문서](https://developer.android.com/guide/topics/ui/custom-components)를 참조하십시오.

<deflist collapsible="true" default-state="collapsed">
<def title="Q) XML 레이아웃에서 하위 호환성을 보장하면서 custom View에 custom 속성을 효율적으로 적용하는 방법은 무엇인가요?">

Custom View에 속성을 추가하려면 `attrs.xml`에 속성을 정의하고, View 생성자에서 이를 파싱해야 합니다. (3번 참고)

**공식 문서에서 지원하는 format 타입**
* `boolean`, `color`, `dimension`, `float`, `fraction`, `integer`, `string`
* `reference` (다른 리소스 참조: @drawable, @string 등)
* `enum`, `flag`

**Android 공식 가이드라인**
* `TypedArray.recycle()`은 반드시 호출해야 합니다. (메모리 누수 방지)
* `try-finally` 블록 사용 권장
* `@JvmOverloads`로 Java 호환성 보장

**하위 호환성 보장 전략**

**1. defStyleAttr과 defStyleRes 활용**

Android에서 Custom View의 스타일을 적용할 때 4가지 우선순위가 존재합니다. 

Android 공식 문서에 따르면 이 우선순위는 다음과 같습니다:

- 가장 높은 우선순위: XML에서 직접 지정한 속성값 (예: `app:cornerRadius="8dp"`)
- 두 번째: XML의 style 속성으로 지정한 스타일 
- 세 번째: defStyleAttr로 참조되는 테마 속성 
- 네 번째: defStyleRes로 지정된 기본 스타일 (API 21 이상)
- 가장 낮은 우선순위: 코드에서 지정한 기본값

`defStyleAttr`은 테마에서 정의된 속성을 참조하는 역할을 합니다.
예를 들어 Material Design의 `Button`은 `R.attr.buttonStyle`이라는 테마 속성을 사용합니다. 
앱의 테마에서 이 속성값을 변경하면 앱 전체의 버튼 스타일이 일괄적으로 변경됩니다.

`defStyleRes`는 API 21(Lollipop)부터 추가된 파라미터로, 테마 속성이 정의되지 않았을 때 사용할 기본 스타일을 직접 지정합니다. 
API 21 미만에서는 이 파라미터가 무시되므로, 하위 호환성을 위해서는 조건부 처리가 필요합니다.

**2. AndroidX 라이브러리를 통한 백포팅**

AndroidX 라이브러리는 새로운 Android 기능을 구버전에서도 사용할 수 있도록 백포팅을 제공합니다. 
Custom View를 만들 때 이러한 호환성 라이브러리를 활용하면 개발자가 직접 API 레벨 체크를 하지 않아도 됩니다.

`AppCompatButton`은 일반 `Button`을 상속하는 대신 사용할 수 있는 호환성 버전입니다. 
이 클래스는 내부적으로 구버전 Android에서도 최신 기능이 동작하도록 처리합니다.

`AppCompatResources`는 벡터 드로어블을 API 14 이상에서 사용할 수 있게 해줍니다. 
원래 벡터 드로어블은 API 21부터 지원되지만, 이 클래스를 사용하면 구버전에서도 자동으로 PNG로 변환되어 표시됩니다.

`ContextCompat`는 색상, 드로어블 등의 리소스를 가져올 때 API 레벨에 관계없이 일관된 방식으로 접근할 수 있게 해줍니다. 
예를 들어 API 23부터 도입된 색상 상태 목록 기능도 구버전에서 사용 가능합니다.

**3. 리소스 한정자를 통한 단계별 기능 제공**

Android는 리소스 한정자 시스템을 통해 특정 API 레벨 이상에서만 사용 가능한 리소스를 정의할 수 있습니다. 
`values-v21`, `values-v23` 같은 폴더를 만들면 해당 API 레벨 이상의 기기에서만 그 리소스가 사용됩니다.

이 방식은 Custom View의 속성 정의에도 적용할 수 있습니다. 
기본 `values` 폴더에는 모든 API 레벨에서 지원되는 기본 속성만 정의하고, `values-v21` 폴더에는 API 21부터 사용 가능한 elevation 같은 속성을 추가로 정의합니다.

빌드 시스템은 자동으로 현재 기기의 API 레벨에 맞는 리소스를 선택합니다.
개발자는 코드에서 별도의 조건문 없이 속성을 사용하되, 해당 속성이 존재하는지 확인하는 방어 코드만 추가하면 됩니다.

</def>
</deflist>