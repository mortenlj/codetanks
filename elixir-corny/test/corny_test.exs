defmodule CornyTest do
  use ExUnit.Case
  doctest Corny

  test "greets the world" do
    assert Corny.hello() == :world
  end
end
