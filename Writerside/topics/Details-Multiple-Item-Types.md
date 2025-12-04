# Details: Multiple Item Types

## 동일한 RecyclerView에 여러 타입의 아이템을 구현하는 방법 {#implement-multiple-item-types-recyclerview}

RecyclerView는 다재다능하며 동일한 목록에 여러 Item Types을 지원합니다. 이를 달성하려면 사용자 지정 Adapter, item view types, 그리고 적절한 레이아웃을 조합하여 사용해야 합니다. 핵심은 항목 유형을 구별하고 올바르게 바인딩하는 데 있습니다.

### Multiple Item Types 구현 단계 {#steps-to-implement-multiple-item-types}

1.  **Item Types 정의**: 각 Item Type은 고유한 식별자(일반적으로 정수 상수)로 표현됩니다. 이 식별자는 Adapter가 뷰 생성 및 바인딩 중에 Item Type을 구별할 수 있도록 합니다.
2.  **getItemViewType() 재정의**: Adapter에서 `getItemViewType()` 메서드를 재정의하여 데이터셋의 각 Item에 대한 적절한 Type을 반환합니다. 이 메서드는 RecyclerView가 인플레이트할 레이아웃 유형을 결정하는 데 도움이 됩니다.
3.  **여러 ViewHolder 처리**: 각 Item Type에 대해 별도의 `ViewHolder` 클래스를 생성합니다. 각 `ViewHolder`는 데이터를 해당 레이아웃에 바인딩하는 역할을 합니다.
4.  **View Type 기반 레이아웃 인플레이트**: `onCreateViewHolder()` 메서드에서 `getItemViewType()`이 반환한 View Type을 기반으로 적절한 레이아웃을 인플레이트합니다.
5.  **그에 따라 데이터 바인딩**: `onBindViewHolder()` 메서드에서 Item Type을 확인하고 해당 `ViewHolder`를 사용하여 데이터를 바인딩합니다.

```kotlin
class MultiTypeAdapter(private val items: List<ListItem>) : RecyclerView.Adapter<RecyclerView.ViewHolder>() {

    companion object {
        const val TYPE_HEADER = 0
        const val TYPE_CONTENT = 1
    }

    override fun getItemViewType(position: Int): Int {
        return when (items[position]) {
            is ListItem.Header -> TYPE_HEADER
            is ListItem.Content -> TYPE_CONTENT
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): RecyclerView.ViewHolder {
        return when (viewType) {
            TYPE_HEADER -> {
                val view = LayoutInflater.from(parent.context).inflate(R.layout.item_header, parent, false)
                HeaderViewHolder(view)
            }
            TYPE_CONTENT -> {
                val view = LayoutInflater.from(parent.context).inflate(R.layout.item_content, parent, false)
                ContentViewHolder(view)
            }
            else-> throw IllegalArgumentException("Invalid view type")
        }
    }

    override fun onBindViewHolder(holder: RecyclerView.ViewHolder, position: Int) {
        when (holder) {
            is HeaderViewHolder -> holder.bind(items[position] as ListItem.Header)
            is ContentViewHolder -> holder.bind(items[position] as ListItem.Content)
        }
    }

    override fun getItemCount(): Int = items.size

    class HeaderViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val title: TextView = itemView.findViewById(R.id.headerTitle)

        fun bind(item: ListItem.Header) {
            title.text = item.title
        }
    }

    class ContentViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val content: TextView = itemView.findViewById(R.id.contentText)

        fun bind(item: ListItem.Content) {
            content.text = item.text
        }
    }
}
```

```kotlin
sealed class ListItem {
    data class Header(val title: String) : ListItem()
    data class Content(val text: String) : ListItem()
}
```

### 주요 참고 사항 {#key-points-to-note}

* **효율성**: RecyclerView는 `ViewHolder`를 재사용하며, 여러 item type을 처리해도 성능이 저하되지 않습니다. 각 item type은 `getItemViewType()` 메서드와 적절한 바인딩을 통해 효율적으로 관리됩니다.
* **명확한 분리**: 각 item type은 자체 레이아웃과 `ViewHolder`를 가지므로, 관심사 분리(separation of concerns)와 깔끔한 코드를 보장합니다.
* **확장성**: 새 item type을 추가하는 데 최소한의 변경만 필요합니다. 새 레이아웃과 `ViewHolder`를 정의하고 `getItemViewType()` 및 `onCreateViewHolder()`의 로직을 조정하기만 하면 됩니다.

### 요약 {#summary}

RecyclerView에서 여러 item type을 구현하려면, 각 item type을 결정하기 위한 `getItemViewType()`, 바인딩을 위한 개별 `ViewHolder`, 그리고 각 type에 대한 고유한 레이아웃을 조합하여 사용해야 합니다. 이 접근 방식은 통합된 목록에서 다양한 콘텐츠를 지원하면서 `RecyclerView`가 효율적이고 확장 가능하도록 보장합니다.