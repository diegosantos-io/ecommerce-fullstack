import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'


function TesteInicial() {
  return <h1>Testes do E-commerce</h1>
}

describe('Configuração dos testes', () => {
  it('renderiza um componente React', () => {
    render(<TesteInicial />)

    expect(
      screen.getByRole('heading', { name: 'Testes do E-commerce' }),
    ).toBeInTheDocument()
  })
})