# Details: 생성자 @JvmOverloads

## 커스텀 뷰의 주 생성자에 @JvmOverloads를 사용할 때 주의해야 하는 이유는 무엇인가요?

Kotlin의 @JvmOverloads 어노테이션은 Kotlin 함수 또는 클래스에 대해 여러 오버로드된 메서드 또는 생성자를 자동으로 생성하여 Kotlin과 Java 간의 상호 운용성을 단순화하는 기능입니다. 
이 기능은 특히 Kotlin의 기본 인수가 관련될 때 유용한데, Java는 기본 인수를 기본적으로 지원하지 않기 때문입니다. 
@JvmOverloads를 사용하면 Kotlin 컴파일러는 컴파일된 바이트코드에 기본값을 가진 매개변수의 가능한 모든 조합을 나타내기 위해 여러 메서드 또는 생성자 시그니처를 생성합니다.

하지만 커스텀 뷰를 구현할 때 @JvmOverloads를 신중하게 사용하지 않으면 의도치 않게 기본 뷰 스타일을 재정의하여 커스텀 뷰의 원래 스타일링이 손실될 수 있습니다.
이는 Button 또는 TextView와 같이 미리 정의된 스타일을 가진 Android 뷰를 확장할 때 특히 문제가 됩니다.

예를 들어, 커스텀 TextInputEditText를 구현할 때 다음과 같이 정의할 수 있습니다.

```kotlin
class ElasticTextInputEditText @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyle: Int = 0
) : TextInputEditText(context, attrs, defStyle) {

}
```

이 예제에서 ElasticTextInputEditText를 일반 TextInputEditText로 사용하면 예상치 못한 동작이나 잠재적인 오류가 발생할 수 있습니다. 
이는 위 코드에서 볼 수 있듯이 `defStyle` 값이 `0`으로 재정의되어 커스텀 뷰가 의도한 스타일링을 잃기 때문입니다.

View가 XML 파일에서 인플레이트될 때, 두 개의 매개변수를 받는 생성자(`Context` 및 `AttributeSet`)가 호출되고, 이 생성자는 세 개의 매개변수를 받는 생성자를 다시 호출합니다.

```java
public ElasticTextInputEditText(Context context, @Nullable AttributeSet attrs) {
    this(context, attrs, 0);
}
```

세 번째 매개변수인 `defStyleAttr`은 커스텀 구현에서 종종 기본적으로 `0`으로 설정됩니다. 
그러나 이 세 개의 매개변수를 받는 생성자의 목적은 [Android 문서](https://developer.android.com/reference/android/view/View#View(android.content.Context,%20android.util.AttributeSet,%20int))에 다음과 같이 설명되어 있습니다.

> XML에서 인플레이션을 수행하고 테마 속성에서 클래스별 기본 스타일을 적용합니다. 
> View의 이 생성자를 통해 서브클래스는 인플레이션될 때 자체 기본 스타일을 사용할 수 있습니다. 
> 예를 들어, `Button` 클래스의 생성자는 슈퍼클래스 생성자의 이 버전을 호출하고 `defStyleAttr`에 `R.attr.buttonStyle`을 제공합니다. 
> 이를 통해 테마의 버튼 스타일은 모든 기본 뷰 속성(특히 배경)뿐만 아니라 `Button` 클래스의 속성까지 수정할 수 있습니다.

적절한 `defStyleAttr` 값(예: `ElasticTextInputEditText`의 경우 `R.attr.editTextStyle`)을 생략하면 커스텀 뷰는 상속된 스타일 구성을 잃을 수 있으며, 이는 XML 인플레이션 중 일관되지 않거나 깨진 동작으로 이어집니다.

TextInputEditText의 내부 구현을 살펴보면, 아래 코드 스니펫에서 볼 수 있듯이 내부적으로 `R.attr.editTextStyle`을 `defStyleAttr`로 사용한다는 것을 알 수 있습니다.

```java
public class TextInputEditText extends AppCompatEditText {

    private final Rect parentRect = new Rect();
    private boolean textInputLayoutFocusedRectEnabled;

    public TextInputEditText(@NonNull Context context) {
        this(context, null);
    }

    public TextInputEditText(@NonNull Context context, @Nullable AttributeSet attrs) {
        this(context, attrs, R.attr.editTextStyle);
    }

    public TextInputEditText(
            @NonNull Context context, @Nullable AttributeSet attrs, int defStyleAttr) { }
}
```

`TextInputEditText`의 구현에서 세 번째 매개변수(`defStyleAttr`)로 `androidx.appcompat.R.attr.editTextStyle`을 전달하는 것을 확인할 수 있습니다. 
이 문제를 해결하고 올바른 스타일링을 보장하기 위해 커스텀 뷰의 생성자에서 `defStyleAttr` 매개변수의 기본값으로 `R.attr.editTextStyle`을 설정하여 수정할 수 있습니다.

```kotlin
class ElasticTextInputEditText @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = androidx.appcompat.R.attr.editTextStyle
) : TextInputEditText(context, attrs, defStyleAttr) {
    // Custom implementation
}
```

`androidx.appcompat.R.attr.editTextStyle`을 기본값으로 명시적으로 할당함으로써, XML 인플레이션 중 커스텀 뷰가 예상되는 기본 스타일을 상속받아 원래 `TextInputEditText`의 동작과 일관성을 유지할 수 있습니다.