declare module 'vuedraggable' {
  import type { DefineComponent } from 'vue'

  export interface DragEvent {
    oldIndex?: number
    newIndex?: number
    item: HTMLElement
    from: HTMLElement
    to: HTMLElement
  }

  export interface DraggableProps {
    modelValue?: any[]
    list?: any[]
    group?: string | object
    itemKey?: string | ((item: any) => string | number)
    clone?: (item: any) => any
    handle?: string
    sort?: boolean
    disabled?: boolean
    animation?: number
    ghostClass?: string
    chosenClass?: string
    dragClass?: string
    forceFallback?: boolean
    fallbackOnBody?: boolean
    fallbackClass?: string
    fallbackTolerance?: number
    scroll?: boolean
    scrollFn?: (
      offsetX: number,
      offsetY: number,
      originalEvent: Event,
      touchEvt: Event,
      hoverTargetEl: HTMLElement,
    ) => 'continue' | void
    scrollSensitivity?: number
    scrollSpeed?: number
    bubbleScroll?: boolean
    draggable?: string
    filter?: string
    preventOnFilter?: boolean
    move?: (
      evt: {
        dragged: HTMLElement
        draggedContext: any
        related: HTMLElement
        relatedContext: any
        from: HTMLElement
        to: HTMLElement
        willInsertAfter: boolean
        isDragging: boolean
      },
      originalEvent: Event,
    ) => boolean | void | 1 | -1
  }

  const Draggable: DefineComponent<DraggableProps>
  export default Draggable
}
